"""FastAPI service for TruthKeeper (Cloud Run).

Endpoints:
    POST /audit       run audit over the corpus, cache in Firestore, return summary
    GET  /report      return all cached audits, sorted worst-first
    GET  /docs-list   return the raw corpus docs (for the UI)
    GET  /healthz     liveness probe
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import audit
import store

CORPUS_PATH = Path(__file__).parent / "seed" / "corpus.json"

app = FastAPI(title="TruthKeeper API", version="0.1.0")

# Permissive CORS: the frontend is a static Firebase Hosting origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _load_corpus() -> list[dict[str, Any]]:
    with CORPUS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


CORPUS: list[dict[str, Any]] = _load_corpus()


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.get("/docs-list")
def docs_list() -> list[dict[str, Any]]:
    return CORPUS


@app.post("/audit")
def run_audit(force: bool = False) -> dict[str, Any]:
    """Run (or refresh) the audit over the whole corpus and cache it."""
    results = audit.audit_corpus(CORPUS, force=force)
    flagged = [r for r in results if r.status != "healthy"]
    return {
        "audited": len(results),
        "flagged": len(flagged),
        "statuses": {r.doc_id: r.status for r in results},
    }


@app.get("/report")
def report() -> dict[str, Any]:
    """Return all cached audits, worst-first. Pure cache read — no model calls."""
    audits = store.get_all_audits()
    audits.sort(key=lambda a: a.get("confidence", 1.0))
    return {"count": len(audits), "audits": audits}
