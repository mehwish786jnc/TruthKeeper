"""Google-only model layer for TruthKeeper.

Exposes a single entry point, ``call_model(layer, prompt)``, that talks to
Gemini (Vertex AI) with an AI-Studio-key / Gemma free-tier fallback. Every
client is Google-family — no non-Google providers are permitted in the product
path.

Errors are normalized so the audit router can make routing decisions:
- ``QuotaError``  -> HTTP 429 / RESOURCE_EXHAUSTED (step down the ladder)
- ``ModelError``  -> anything else (bad response, auth, network)
"""

from __future__ import annotations

import os
from enum import Enum

from google import genai
from google.genai import types


class Layer(str, Enum):
    """Routing-ladder layers backed by a live model."""

    FLASH = "flash"   # Layer 1: primary, cheap
    PRO = "pro"       # Layer 2: escalation for hard docs
    GEMMA = "gemma"   # Layer 3: free fallback (open Google-family model)


class ModelError(Exception):
    """A model call failed for a non-quota reason."""


class QuotaError(ModelError):
    """A model call hit a rate/quota limit (HTTP 429)."""


def _model_name(layer: Layer) -> str:
    return {
        Layer.FLASH: os.getenv("MODEL_FLASH", "gemini-2.5-flash"),
        Layer.PRO: os.getenv("MODEL_PRO", "gemini-2.5-pro"),
        Layer.GEMMA: os.getenv("MODEL_GEMMA", "gemma-3-27b-it"),
    }[layer]


def _vertex_client() -> genai.Client:
    """Primary path: Vertex AI (uses the Cloud Run service account)."""
    return genai.Client(
        vertexai=True,
        project=os.environ["GCP_PROJECT"],
        location=os.getenv("GCP_LOCATION", "us-central1"),
    )


def _studio_client() -> genai.Client:
    """Fallback path: AI Studio free-tier API key."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ModelError("GEMINI_API_KEY not set; cannot use free-tier fallback")
    return genai.Client(api_key=key)


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "resource_exhausted" in text or "quota" in text


def call_model(layer: Layer, prompt: str, *, use_studio: bool = False) -> str:
    """Call a Google model and return raw JSON text.

    ``use_studio=True`` forces the AI Studio free-tier key (Layer 3). Gemma is
    only available via AI Studio, so it always uses that client.
    """
    try:
        client = _studio_client() if (use_studio or layer == Layer.GEMMA) else _vertex_client()
        response = client.models.generate_content(
            model=_model_name(layer),
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ModelError(f"{layer} returned an empty response")
        return text
    except (QuotaError, ModelError):
        raise
    except Exception as exc:  # noqa: BLE001 - normalize SDK/transport errors
        if _is_quota_error(exc):
            raise QuotaError(str(exc)) from exc
        raise ModelError(str(exc)) from exc
