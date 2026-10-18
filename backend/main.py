"""FastAPI service for TruthKeeper (Cloud Run).

Documents live in Firestore (the ``documents`` collection) and are the dynamic
corpus the app audits. On first startup the collection is seeded from the on-disk
``seed/corpus.json`` (with owners from ``seed/owners.json``); after that, uploads
and deletes mutate Firestore directly.

Key endpoints:
    GET    /documents            list the corpus (from Firestore, disk fallback)
    POST   /documents            upload a doc (text or PDF) -> save -> audit
    DELETE /documents/{id}       remove a doc and its cached audit
    POST   /documents/{id}/audit re-audit one doc
    POST   /audit                audit the whole corpus, cache it
    GET    /report               cached audits, worst-first
    GET    /graph /verify /health-score /decisions /ask /research /impact /remediate
    GET    /insights             authored dashboard content (gaps/processes/relationships)
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import audit
import insights
import store

SEED_DIR = Path(__file__).parent / "seed"
CORPUS_PATH = SEED_DIR / "corpus.json"
OWNERS_PATH = SEED_DIR / "owners.json"
INSIGHTS_PATH = SEED_DIR / "insights.json"

app = FastAPI(title="TruthKeeper API", version="0.2.0")

# Permissive CORS: the frontend is a static Firebase Hosting origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# corpus sourcing: Firestore first, on-disk seed as fallback
# --------------------------------------------------------------------------- #
def _load_seed(path: Path, default: Any) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return default


def _load_corpus() -> list[dict[str, Any]]:
    """The on-disk seed corpus (fallback when Firestore is empty/unavailable)."""
    return _load_seed(CORPUS_PATH, [])


def get_corpus() -> list[dict[str, Any]]:
    """Return the live corpus from Firestore, falling back to the on-disk seed."""
    try:
        docs = store.get_all_documents()
        if docs:
            return docs
    except Exception:  # noqa: BLE001 - Firestore unavailable -> use disk copy
        pass
    return _load_corpus()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug or f"doc-{int(datetime.now(timezone.utc).timestamp())}"


def _reaudit_conflicts(result: Any, corpus: list[dict[str, Any]]) -> list[str]:
    """Re-audit the existing documents that ``result`` says it contradicts, so a
    new/changed document's conflict is reflected on BOTH sides (not just its own
    card). Bounded: only the directly-named docs, one level deep — not the whole
    corpus. Returns the ids that were re-audited."""
    by_id = {d["id"]: d for d in corpus}
    done: list[str] = []
    for c in result.contradictions:
        other = getattr(c, "other_doc", "")
        if other and other != result.doc_id and other in by_id and other not in done:
            try:
                audit.audit_document(by_id[other], corpus, force=True)
                done.append(other)
            except Exception:  # noqa: BLE001 - one bad re-audit shouldn't fail the request
                pass
    return done


# --------------------------------------------------------------------------- #
# one-time seeding of Firestore from the on-disk seeds
# --------------------------------------------------------------------------- #
@app.on_event("startup")
def seed_firestore() -> None:
    """Populate Firestore from the on-disk seeds if the collections are empty.

    Idempotent and best-effort: never crashes the app if Firestore is briefly
    unavailable (the endpoints fall back to the disk copies anyway).
    """
    try:
        if not store.get_all_documents():
            owners = _load_seed(OWNERS_PATH, {})
            for doc in _load_corpus():
                doc = {**doc, "owner": owners.get(doc["id"], {"team": "", "poc": ""})}
                store.save_document(doc["id"], doc)
    except Exception:  # noqa: BLE001
        pass
    # Insights are authored seed content (repo = source of truth): always refresh.
    try:
        store.save_insights(_load_seed(INSIGHTS_PATH, {}))
    except Exception:  # noqa: BLE001
        pass


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


class ApplyFixIn(BaseModel):
    revised_body: str
    change_summary: str = ""


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


# --------------------------------------------------------------------------- #
# documents (dynamic corpus)
# --------------------------------------------------------------------------- #
@app.get("/documents")
def list_documents() -> list[dict[str, Any]]:
    """The live corpus (Firestore, disk fallback)."""
    return get_corpus()


@app.get("/docs-list")
def docs_list() -> list[dict[str, Any]]:
    """Alias of GET /documents (kept for backwards compatibility)."""
    return get_corpus()


def _extract_text(filename: str, raw: bytes) -> str:
    """Pull text out of an uploaded file (.pdf via pypdf, else decode as text)."""
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader  # local import: optional dependency
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    return raw.decode("utf-8", errors="replace").strip()


@app.post("/documents")
async def create_document(
    title: str | None = Form(None),
    body: str | None = Form(None),
    source: str = Form(""),
    owner: str = Form(""),
    poc: str = Form(""),
    last_updated: str = Form(""),
    file: UploadFile | None = File(None),
) -> dict[str, Any]:
    """Upload a document (pasted text or a .txt/.md/.pdf file), save it, and audit it."""
    if file is not None:
        raw = await file.read()
        body = _extract_text(file.filename or "upload", raw)
        if not title:
            title = Path(file.filename or "upload").stem.replace("-", " ").replace("_", " ").title()
        if not source:
            source = file.filename or ""
    if not title or not body:
        raise HTTPException(status_code=400, detail="A title and body (or a file) are required.")

    doc_id = _slugify(source or title)
    doc = {
        "id": doc_id,
        "title": title,
        "source": source or f"{doc_id}.md",
        "last_updated": last_updated.strip() or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "body": body,
        "owner": {"team": owner.strip(), "poc": poc.strip()},
    }
    store.save_document(doc_id, doc)

    # Audit the new doc against the full (now-updated) corpus, then re-audit just
    # the existing docs it conflicts with so the clash shows on both sides.
    corpus = get_corpus()
    result = audit.audit_document(doc, corpus, force=True)
    reaudited = _reaudit_conflicts(result, corpus)
    return {"ok": True, "document": doc, "audit": result.model_dump(), "reaudited": reaudited}


@app.delete("/documents/{doc_id}")
def delete_document(doc_id: str) -> dict[str, Any]:
    """Remove a document and its cached audit."""
    if store.get_document(doc_id) is None:
        raise HTTPException(status_code=404, detail=f"No document '{doc_id}'.")
    store.delete_document(doc_id)
    store.delete_audit(doc_id)
    return {"ok": True, "deleted": doc_id}


@app.post("/documents/{doc_id}/audit")
def reaudit_document(doc_id: str) -> dict[str, Any]:
    """Re-audit a single document (force, bypassing the cache)."""
    doc = store.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"No document '{doc_id}'.")
    corpus = get_corpus()
    result = audit.audit_document(doc, corpus, force=True)
    reaudited = _reaudit_conflicts(result, corpus)
    return {"ok": True, "audit": result.model_dump(), "reaudited": reaudited}


@app.post("/documents/{doc_id}/propose-fix")
def propose_fix(doc_id: str) -> dict[str, Any]:
    """Generate (but DO NOT save) an AI rewrite that resolves the doc's flagged
    issue, so a human can review the before/after before applying it."""
    doc = store.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"No document '{doc_id}'.")
    audit_record = store.get_audit(doc_id) or {}
    if audit_record.get("status") == "healthy":
        return {"ok": True, "already_healthy": True}
    fix = insights.rewrite_to_resolve(doc, audit_record, get_corpus())
    if not fix:
        raise HTTPException(status_code=502,
                            detail="Could not draft an automatic fix — edit the document manually.")
    return {
        "ok": True, "doc_id": doc_id,
        "status": audit_record.get("status", "uncertain"),
        "current_body": doc.get("body", ""),
        "revised_body": fix["revised_body"],
        "change_summary": fix["change_summary"],
    }


@app.post("/documents/{doc_id}/apply-fix")
def apply_fix(doc_id: str, body: ApplyFixIn) -> dict[str, Any]:
    """Save a human-approved rewrite, then re-audit the document and the ones it
    conflicted with so the resolution persists and shows on every side."""
    doc = store.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"No document '{doc_id}'.")
    if not body.revised_body.strip():
        raise HTTPException(status_code=400, detail="revised_body is required.")

    audit_record = store.get_audit(doc_id) or {}
    prior_conflicts = [c.get("other_doc", "") for c in (audit_record.get("contradictions") or [])]

    doc["body"] = body.revised_body
    doc["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    store.save_document(doc_id, doc)

    corpus = get_corpus()  # now reflects the rewritten document
    result = audit.audit_document(doc, corpus, force=True)

    reaudited = []
    for other in prior_conflicts:
        od = store.get_document(other)
        if od and other != doc_id:
            try:
                audit.audit_document(od, corpus, force=True)
                reaudited.append(other)
            except Exception:  # noqa: BLE001
                pass

    return {"ok": True, "document": doc, "audit": result.model_dump(), "reaudited": reaudited}


@app.post("/audit")
def run_audit(force: bool = False) -> dict[str, Any]:
    """Run (or refresh) the audit over the whole corpus and cache it."""
    results = audit.audit_corpus(get_corpus(), force=force)
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
    return insights.build_graph(get_corpus())


@app.get("/verify")
def verify(doc_id: str) -> dict[str, Any]:
    """Trust API: is a document safe to rely on? (cache read)"""
    return insights.verify(doc_id)


@app.get("/health-score")
def health_score() -> dict[str, Any]:
    """Org-level knowledge-health KPI + breakdown + trend."""
    return insights.health_score()


@app.get("/insights")
def get_insights() -> dict[str, Any]:
    """Authored dashboard content (gaps / processes / relationships)."""
    data = None
    try:
        data = store.get_insights()
    except Exception:  # noqa: BLE001 - Firestore unavailable -> disk fallback
        pass
    return data or _load_seed(INSIGHTS_PATH, {})


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
    return insights.ask(body.question, get_corpus())


@app.post("/research")
def research(body: AskIn) -> dict[str, Any]:
    """Research & Decision: compare evidence, surface contradictions/gaps, recommend."""
    return insights.research(body.question, get_corpus())


# --------------------------------------------------------------------------- #
# ACT: impact / remediate
# --------------------------------------------------------------------------- #
@app.post("/impact")
def impact(body: DocIn) -> dict[str, Any]:
    """Impact Analysis: documents affected if this one changes."""
    return insights.impact(body.doc_id, get_corpus())


@app.post("/remediate")
def remediate(body: DocIn) -> dict[str, Any]:
    """Remediation: turn an identified problem into an approvable action."""
    return insights.remediate(body.doc_id, get_corpus())
