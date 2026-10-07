"""FastAPI service for TruthKeeper (Cloud Run).

Endpoints:
    POST /audit       run audit over the corpus, cache in Firestore, return summary
    GET  /report      return all cached audits, sorted worst-first
    GET  /docs-list   return the raw corpus docs (for the UI)
    GET  /healthz     liveness probe
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import audit
import insights
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


# --------------------------------------------------------------------------- #
# request bodies
# --------------------------------------------------------------------------- #
class AskIn(BaseModel):
    question: str


class DocIn(BaseModel):
    doc_id: str


class DecisionIn(BaseModel):
    doc_id: str
    action: str  # "accept" | "dismiss"
    note: str = ""


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
    """Return all cached audits, worst-first, annotated with any human decision.
    Pure cache read — no model calls."""
    audits = store.get_all_audits()
    decisions = store.get_all_decisions()
    for a in audits:
        a["decision"] = decisions.get(a.get("doc_id"))
    audits.sort(key=lambda a: a.get("confidence", 1.0))
    return {"count": len(audits), "audits": audits}


# --------------------------------------------------------------------------- #
# TRUST: graph / verify / health
# --------------------------------------------------------------------------- #
@app.get("/graph")
def graph() -> dict[str, Any]:
    """Knowledge-health graph: document nodes + contradiction edges."""
    return insights.build_graph(CORPUS)


@app.get("/verify")
def verify(doc_id: str) -> dict[str, Any]:
    """Trust API: is a document safe to rely on? (cache read)"""
    return insights.verify(doc_id)


@app.get("/health-score")
def health_score() -> dict[str, Any]:
    """Org-level knowledge-health KPI + breakdown + trend."""
    return insights.health_score()


# --------------------------------------------------------------------------- #
# decisions (human-in-the-loop)
# --------------------------------------------------------------------------- #
@app.get("/decisions")
def get_decisions() -> dict[str, Any]:
    return {"decisions": store.get_all_decisions()}


@app.post("/decisions")
def post_decision(body: DecisionIn) -> dict[str, Any]:
    payload = {"action": body.action, "note": body.note,
               "decided_at": datetime.now(timezone.utc).isoformat()}
    store.save_decision(body.doc_id, payload)
    return {"ok": True, "doc_id": body.doc_id, **payload}


# --------------------------------------------------------------------------- #
# UNDERSTAND: ask / research
# --------------------------------------------------------------------------- #
@app.post("/ask")
def ask(body: AskIn) -> dict[str, Any]:
    """Guardrailed answer: retrieve a source, gate the answer on its trust."""
    return insights.ask(body.question, CORPUS)


@app.post("/research")
def research(body: AskIn) -> dict[str, Any]:
    """Research & Decision: compare evidence, surface contradictions/gaps, recommend."""
    return insights.research(body.question, CORPUS)


# --------------------------------------------------------------------------- #
# ACT: impact / remediate
# --------------------------------------------------------------------------- #
@app.post("/impact")
def impact(body: DocIn) -> dict[str, Any]:
    """Impact Analysis: documents affected if this one changes."""
    return insights.impact(body.doc_id, CORPUS)


@app.post("/remediate")
def remediate(body: DocIn) -> dict[str, Any]:
    """Remediation: turn an identified problem into an approvable action."""
    return insights.remediate(body.doc_id, CORPUS)
