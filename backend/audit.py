"""Audit engine: prompt building, routing ladder, and cache-first auditing.

Routing ladder (resilience, try top first):
    Layer 0: Firestore cache
    Layer 1: Gemini Flash
    Layer 2: Gemini Pro        (escalate if confidence < 0.55 or status uncertain)
    Layer 3: Gemini free tier / Gemma  (on quota)
    Layer 4: rule-based heuristics     (never-fails floor)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

import store
from models import Layer, ModelError, QuotaError, call_model

ESCALATION_THRESHOLD = 0.55

Status = Literal["healthy", "stale", "contradictory", "deprecated", "uncertain"]

DEPRECATED_TERMS = [
    "stackdriver", "nagios", "python 2", "python2", "heroku",
    "angular.js", "angularjs", "flash player", "centos 6",
]


# --------------------------------------------------------------------------- #
# Contract
# --------------------------------------------------------------------------- #
class Contradiction(BaseModel):
    other_doc: str = ""
    explanation: str = ""
    evidence: str = ""


class AuditResult(BaseModel):
    doc_id: str = ""
    title: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    status: Status = "uncertain"
    contradictions: list[Contradiction] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    suggested_fix: str = ""
    model_used: str = ""
    created_at: str = ""


# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #
def build_prompt(doc: dict[str, Any], corpus: list[dict[str, Any]]) -> str:
    """Build the auditing prompt: the target doc + the rest of the corpus."""
    others = [d for d in corpus if d["id"] != doc["id"]]
    context = "\n\n".join(
        f"[{d['id']}] {d['title']} (updated {d.get('last_updated', '?')})\n{d['body']}"
        for d in others
    )
    return f"""You are TruthKeeper, a knowledge-base auditor. You do NOT answer
from documents — you INTERROGATE them. Audit the TARGET document against the
rest of the corpus for contradictions, stale content, and deprecated references.

Return ONLY JSON matching exactly this schema:
{{
  "confidence": 0.0-1.0,
  "status": "healthy" | "stale" | "contradictory" | "deprecated" | "uncertain",
  "contradictions": [{{"other_doc": "<doc id>", "explanation": "...", "evidence": "..."}}],
  "evidence": ["quoted clause/line that triggered the flag"],
  "suggested_fix": "..."
}}
Rule: if evidence is insufficient, return status "uncertain" — DO NOT guess.
Today's date is {datetime.now(timezone.utc):%Y-%m-%d}.

TARGET DOCUMENT [{doc['id']}] {doc['title']} (updated {doc.get('last_updated', '?')}):
{doc['body']}

REST OF CORPUS:
{context}
"""


# --------------------------------------------------------------------------- #
# Heuristic floor (Layer 4) — never fails
# --------------------------------------------------------------------------- #
def _heuristic_audit(doc: dict[str, Any]) -> AuditResult:
    body_lc = doc["body"].lower()
    evidence: list[str] = []
    status: Status = "healthy"
    confidence = 0.5

    found = [t for t in DEPRECATED_TERMS if t in body_lc]
    if found:
        status = "deprecated"
        confidence = 0.6
        evidence.append(f"References deprecated tooling: {', '.join(found)}")

    last_updated = str(doc.get("last_updated", ""))
    match = re.match(r"(\d{4})", last_updated)
    if match:
        age_years = datetime.now(timezone.utc).year - int(match.group(1))
        if age_years >= 2:
            if status == "healthy":
                status = "stale"
            confidence = 0.6
            evidence.append(f"Not updated since {last_updated} (~{age_years}y old)")

    return AuditResult(
        doc_id=doc["id"],
        title=doc["title"],
        confidence=confidence,
        status=status,
        evidence=evidence,
        suggested_fix="Review manually (heuristic fallback — model unavailable).",
        model_used="heuristic",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #
def _parse(raw: str, doc: dict[str, Any], model_used: str) -> AuditResult:
    data = json.loads(raw)
    result = AuditResult(**data)
    result.doc_id = doc["id"]
    result.title = doc["title"]
    result.model_used = model_used
    result.created_at = datetime.now(timezone.utc).isoformat()
    return result


# --------------------------------------------------------------------------- #
# Routing ladder
# --------------------------------------------------------------------------- #
def _run_ladder(doc: dict[str, Any], corpus: list[dict[str, Any]]) -> AuditResult:
    prompt = build_prompt(doc, corpus)

    # Layer 1: Flash
    try:
        result = _parse(call_model(Layer.FLASH, prompt), doc, "gemini-flash")
        # Layer 2: escalate hard docs to Pro
        if result.confidence < ESCALATION_THRESHOLD or result.status == "uncertain":
            try:
                return _parse(call_model(Layer.PRO, prompt), doc, "gemini-pro")
            except (QuotaError, ModelError):
                return result  # keep the Flash answer if Pro is unavailable
        return result
    except QuotaError:
        pass  # fall through to free tier
    except (ModelError, json.JSONDecodeError, ValidationError):
        pass  # fall through to free tier / heuristic

    # Layer 3: free tier / Gemma
    try:
        return _parse(call_model(Layer.GEMMA, prompt, use_studio=True), doc, "gemma")
    except (QuotaError, ModelError, json.JSONDecodeError, ValidationError):
        pass

    # Layer 4: heuristic floor
    return _heuristic_audit(doc)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def audit_document(
    doc: dict[str, Any],
    corpus: list[dict[str, Any]],
    *,
    force: bool = False,
) -> AuditResult:
    """Cache-first audit of a single document.

    Reads Firestore (Layer 0) unless ``force=True``; otherwise runs the ladder
    and caches the result.
    """
    if not force:
        cached = store.get_audit(doc["id"])
        if cached:
            return AuditResult(**cached)

    result = _run_ladder(doc, corpus)
    store.save_audit(doc["id"], result.model_dump())
    return result


def audit_corpus(
    corpus: list[dict[str, Any]],
    *,
    force: bool = False,
) -> list[AuditResult]:
    """Audit every document; returns results sorted worst-first (low confidence)."""
    results = [audit_document(doc, corpus, force=force) for doc in corpus]
    return sorted(results, key=lambda r: r.confidence)
