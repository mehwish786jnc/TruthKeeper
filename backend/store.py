"""Firestore read/write for cached audit results.

The ``audits`` collection is the cache-first core: each document is audited once
and the result lives here, keyed by ``doc_id``. The live app reads from here and
never triggers a model call.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from google.cloud import firestore

AUDITS_COLLECTION = "audits"


@lru_cache(maxsize=1)
def _db() -> firestore.Client:
    return firestore.Client(project=os.environ["GCP_PROJECT"])


def get_audit(doc_id: str) -> dict[str, Any] | None:
    """Return the cached audit for ``doc_id``, or ``None`` if not cached."""
    snap = _db().collection(AUDITS_COLLECTION).document(doc_id).get()
    return snap.to_dict() if snap.exists else None


def save_audit(doc_id: str, payload: dict[str, Any]) -> None:
    """Write (overwrite) the cached audit for ``doc_id``."""
    _db().collection(AUDITS_COLLECTION).document(doc_id).set(payload)


def get_all_audits() -> list[dict[str, Any]]:
    """Return every cached audit. Used by GET /report."""
    return [snap.to_dict() for snap in _db().collection(AUDITS_COLLECTION).stream()]
