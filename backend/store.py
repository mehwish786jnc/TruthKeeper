"""Firestore read/write for cached audits, documents, decisions, and insights.

Collections:
- ``documents``  the knowledge base itself (the corpus) — dynamic, keyed by doc id.
- ``audits``     cached audit results, keyed by ``doc_id`` (the cache-first core).
- ``decisions``  human accept/dismiss decisions, keyed by ``doc_id``.
- ``insights``   authored dashboard content (gaps / processes / relationships), single doc.

The live app reads documents + cached audits from here and never triggers a model
call on the render path.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from google.cloud import firestore

DOCUMENTS_COLLECTION = "documents"
AUDITS_COLLECTION = "audits"
DECISIONS_COLLECTION = "decisions"
INSIGHTS_COLLECTION = "insights"
INSIGHTS_DOC_ID = "default"


@lru_cache(maxsize=1)
def _db() -> firestore.Client:
    return firestore.Client(project=os.environ["GCP_PROJECT"])


# --------------------------------------------------------------------------- #
# documents (the corpus)
# --------------------------------------------------------------------------- #
def get_document(doc_id: str) -> dict[str, Any] | None:
    """Return a single document, or ``None`` if it doesn't exist."""
    snap = _db().collection(DOCUMENTS_COLLECTION).document(doc_id).get()
    return snap.to_dict() if snap.exists else None


def save_document(doc_id: str, payload: dict[str, Any]) -> None:
    """Write (overwrite) a document. ``payload`` must carry its own ``id``."""
    _db().collection(DOCUMENTS_COLLECTION).document(doc_id).set(payload)


def get_all_documents() -> list[dict[str, Any]]:
    """Return every document (the corpus). Empty list if none/unavailable."""
    return [snap.to_dict() for snap in _db().collection(DOCUMENTS_COLLECTION).stream()]


def delete_document(doc_id: str) -> None:
    """Delete a document."""
    _db().collection(DOCUMENTS_COLLECTION).document(doc_id).delete()


# --------------------------------------------------------------------------- #
# audits (cache-first core)
# --------------------------------------------------------------------------- #
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


def delete_audit(doc_id: str) -> None:
    """Delete the cached audit for ``doc_id`` (e.g. when its document is removed)."""
    _db().collection(AUDITS_COLLECTION).document(doc_id).delete()


# --------------------------------------------------------------------------- #
# decisions (human-in-the-loop)
# --------------------------------------------------------------------------- #
def save_decision(doc_id: str, payload: dict[str, Any]) -> None:
    """Persist a human decision (accept/dismiss a fix) for a document."""
    _db().collection(DECISIONS_COLLECTION).document(doc_id).set(payload)


def get_all_decisions() -> dict[str, Any]:
    """Return all decisions keyed by doc_id. Used to annotate /report."""
    out: dict[str, Any] = {}
    for snap in _db().collection(DECISIONS_COLLECTION).stream():
        out[snap.id] = snap.to_dict()
    return out


# --------------------------------------------------------------------------- #
# insights (authored dashboard content: gaps / processes / relationships)
# --------------------------------------------------------------------------- #
def get_insights() -> dict[str, Any] | None:
    """Return the authored insights doc, or ``None`` if not seeded."""
    snap = _db().collection(INSIGHTS_COLLECTION).document(INSIGHTS_DOC_ID).get()
    return snap.to_dict() if snap.exists else None


def save_insights(payload: dict[str, Any]) -> None:
    """Write (overwrite) the authored insights doc."""
    _db().collection(INSIGHTS_COLLECTION).document(INSIGHTS_DOC_ID).set(payload)
