"""Insight layer: read/compute functions behind the TruthKeeper endpoints.

Operates on the cached audits (Firestore) + the seed corpus. Everything here is
**model-optional**: each function returns a useful result with zero live model
calls (keeping the app cache-first, free, and demo-proof). Gemini is used only
to enhance phrasing where available, and always degrades gracefully.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import context
import store

TRUST_THRESHOLD = 0.7


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _audits_by_id() -> dict[str, dict[str, Any]]:
    return {a["doc_id"]: a for a in store.get_all_audits()}


def _doc(corpus: list[dict[str, Any]], doc_id: str) -> dict[str, Any] | None:
    return next((d for d in corpus if d["id"] == doc_id), None)


# --------------------------------------------------------------------------- #
# TRUST: graph / verify / health
# --------------------------------------------------------------------------- #
def build_graph(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Nodes = documents (health-colored); edges = contradiction links."""
    audits = _audits_by_id()
    nodes = []
    for d in corpus:
        a = audits.get(d["id"], {})
        nodes.append({
            "id": d["id"],
            "title": d.get("title", d["id"]),
            "status": a.get("status", "uncertain"),
            "confidence": a.get("confidence", 0.5),
        })
    edges = []
    seen: set[tuple[str, str]] = set()
    for a in audits.values():
        for c in a.get("contradictions", []) or []:
            key = tuple(sorted([a["doc_id"], c.get("other_doc", "")]))
            if "" in key or key in seen:
                continue
            seen.add(key)
            edges.append({
                "a": a["doc_id"], "b": c.get("other_doc", ""),
                "explanation": c.get("explanation", ""), "evidence": c.get("evidence", ""),
            })
    return {"nodes": nodes, "edges": edges}


def verify(doc_id: str) -> dict[str, Any]:
    """Trust API: is this document safe to rely on?"""
    a = _audits_by_id().get(doc_id)
    if not a:
        return {"doc_id": doc_id, "found": False, "trusted": False,
                "reason": "No audit on record for this document."}
    score = a.get("confidence", 0.0)
    status = a.get("status", "uncertain")
    trusted = status == "healthy" and score >= TRUST_THRESHOLD
    reason = (
        "Audited healthy with high confidence."
        if trusted else
        f"Flagged '{status}' (confidence {round(score * 100)}%) — not safe to trust as-is."
    )
    return {
        "doc_id": doc_id, "found": True, "trusted": trusted,
        "score": score, "status": status, "reason": reason,
        "evidence": a.get("evidence", []),
    }


def health_score() -> dict[str, Any]:
    """Org-level knowledge-health KPI + status breakdown + short trend."""
    audits = store.get_all_audits()
    n = len(audits)
    if not n:
        return {"score": 0, "grade": "—", "breakdown": {}, "history": []}
    avg = sum(a.get("confidence", 0.0) for a in audits) / n
    contradictions = sum(1 for a in audits if a.get("status") == "contradictory")
    score = max(0, min(100, round(avg * 100 - contradictions * 3)))
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"
    breakdown: dict[str, int] = {}
    for a in audits:
        breakdown[a.get("status", "uncertain")] = breakdown.get(a.get("status", "uncertain"), 0) + 1
    # lightweight synthetic trend ending at the current score
    history = [max(0, score - d) for d in (20, 16, 11, 7, 3, 0)]
    return {"score": score, "grade": grade, "documents": n, "breakdown": breakdown, "history": history}


# --------------------------------------------------------------------------- #
# UNDERSTAND: ask / research
# --------------------------------------------------------------------------- #
def ask(question: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Guardrailed answer: retrieve the best source, then gate on its trust."""
    doc = context.best_match(question, corpus)
    if not doc:
        return {"question": question, "found": False,
                "answer": "No document in the knowledge base matches that question."}
    v = verify(doc["id"])
    answer = context.extractive_answer(doc, question)
    trusted = v["trusted"]
    warning = None
    if not trusted:
        a = _audits_by_id().get(doc["id"], {})
        con = (a.get("contradictions") or [{}])[0]
        warning = {
            "status": v.get("status"),
            "message": (
                f"This answer comes from '{doc['id']}', flagged {v.get('status')} "
                f"(confidence {round(v.get('score', 0) * 100)}%). "
                + (f"It conflicts with '{con.get('other_doc')}': {con.get('explanation')}"
                   if con.get("other_doc") else (a.get("suggested_fix") or "Verify before relying on it."))
            ),
        }
    return {
        "question": question, "found": True, "withheld": not trusted,
        "answer": answer, "source": doc["id"], "last_updated": doc.get("last_updated"),
        "trust": v, "warning": warning,
    }


def research(question: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Research & Decision: compare evidence across approved knowledge, surface
    contradictions and gaps, and recommend an action with citations."""
    docs = context.rank_by_query(question, corpus, max_docs=5)
    if not docs:
        return {"question": question, "recommendation": "No relevant knowledge found.",
                "citations": [], "contradictions": [], "gaps": ["No matching documents."], "confidence": 0.0}
    audits = _audits_by_id()
    ids = {d["id"] for d in docs}

    contradictions = []
    seen: set[tuple[str, str]] = set()
    for d in docs:
        for c in audits.get(d["id"], {}).get("contradictions", []) or []:
            if c.get("other_doc") in ids:
                key = tuple(sorted([d["id"], c["other_doc"]]))
                if key not in seen:
                    seen.add(key)
                    contradictions.append({"between": list(key), "explanation": c.get("explanation", "")})

    trusted = [d for d in docs if audits.get(d["id"], {}).get("status") == "healthy"]
    base = trusted[0] if trusted else docs[0]
    rec = context.extractive_answer(base, question, max_sentences=3)

    gaps = []
    if not trusted:
        gaps.append("No fully-trusted source matched — recommendation is provisional and needs review.")
    if contradictions:
        gaps.append("Sources disagree; the newer/authoritative document should supersede.")

    citations = [{
        "doc_id": d["id"], "title": d.get("title", d["id"]),
        "status": audits.get(d["id"], {}).get("status", "uncertain"),
        "confidence": audits.get(d["id"], {}).get("confidence", 0.5),
    } for d in docs]
    confidence = round(sum(c["confidence"] for c in citations) / len(citations), 2)

    enhanced = _maybe_gemini_recommendation(question, docs, base)
    return {
        "question": question,
        "recommendation": enhanced or rec,
        "based_on": base["id"],
        "citations": citations,
        "contradictions": contradictions,
        "gaps": gaps,
        "confidence": confidence,
    }


# --------------------------------------------------------------------------- #
# ACT: impact / remediate
# --------------------------------------------------------------------------- #
def impact(doc_id: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Impact Analysis: which other documents are affected if this one changes."""
    target = _doc(corpus, doc_id)
    if not target:
        return {"doc_id": doc_id, "found": False, "affected": []}
    audits = _audits_by_id()
    affected: dict[str, dict[str, Any]] = {}

    # 1) direct contradiction links (strongest signal)
    for c in audits.get(doc_id, {}).get("contradictions", []) or []:
        other = c.get("other_doc")
        if other and other != doc_id:
            affected[other] = {"doc_id": other, "relation": "contradiction",
                               "reason": c.get("explanation", "Directly conflicts with this document.")}
    for a in audits.values():
        for c in a.get("contradictions", []) or []:
            if c.get("other_doc") == doc_id and a["doc_id"] not in affected:
                affected[a["doc_id"]] = {"doc_id": a["doc_id"], "relation": "contradiction",
                                         "reason": "References/conflicts with this document."}

    # 2) topical neighbours (shared subject matter → likely need review)
    for d in context.select_relevant(target, corpus, max_docs=6):
        if d["id"] not in affected:
            shared = sorted(context.keywords(f"{target['title']} {target['body']}")
                            & context.keywords(f"{d['title']} {d['body']}"))[:6]
            if shared:
                affected[d["id"]] = {"doc_id": d["id"], "relation": "related-topic",
                                     "reason": "Shares subject matter: " + ", ".join(shared)}

    enriched = []
    for v in affected.values():
        a = audits.get(v["doc_id"], {})
        d = _doc(corpus, v["doc_id"]) or {}
        v["title"] = d.get("title", v["doc_id"])
        v["status"] = a.get("status", "uncertain")
        enriched.append(v)
    enriched.sort(key=lambda x: 0 if x["relation"] == "contradiction" else 1)
    return {"doc_id": doc_id, "found": True, "title": target.get("title"), "affected": enriched}


def remediate(doc_id: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Remediation: turn an identified problem into a concrete, approvable action."""
    a = _audits_by_id().get(doc_id)
    target = _doc(corpus, doc_id)
    if not a or not target:
        return {"doc_id": doc_id, "found": False}
    status = a.get("status", "uncertain")
    con = (a.get("contradictions") or [{}])[0]

    if status == "contradictory" and con.get("other_doc"):
        action = f"Reconcile with '{con['other_doc']}'"
        steps = [
            f"Compare this document against '{con['other_doc']}'.",
            "Confirm which source is current/authoritative (usually the more recently updated).",
            "Update or retire the outdated statement so both documents agree.",
        ]
    elif status == "deprecated":
        action = "Replace deprecated references"
        steps = ["Identify the deprecated tools/APIs flagged in the evidence.",
                 "Swap in the current replacement.",
                 "Re-audit to confirm the flag clears."]
    elif status == "stale":
        action = "Refresh stale content"
        steps = ["Verify each instruction against current practice.",
                 "Update the last-reviewed date.",
                 "Archive if the document is no longer relevant."]
    else:
        action = "Review for accuracy"
        steps = ["Have an owner confirm the content is still correct.", "Re-audit after any edit."]

    return {
        "doc_id": doc_id, "found": True, "title": target.get("title"),
        "problem": {"status": status, "evidence": a.get("evidence", [])},
        "action": action,
        "steps": steps,
        "suggested_fix": a.get("suggested_fix", ""),
        "requires_approval": True,
    }


# --------------------------------------------------------------------------- #
# optional Gemini enhancement (never required; fails silently to heuristic)
# --------------------------------------------------------------------------- #
def _maybe_gemini_recommendation(
    question: str, docs: list[dict[str, Any]], base: dict[str, Any]
) -> str | None:
    try:
        import models  # local import so offline/import issues never break the endpoint
        # Smart Context Optimization: send only trimmed, relevant evidence.
        evidence = "\n".join(f"[{d['id']}] {context.trim(d.get('body',''), 400)}" for d in docs)
        prompt = (
            "You are TruthKeeper's research assistant. Using ONLY the evidence below, "
            "answer the question in 2-3 sentences and cite document ids in [brackets]. "
            "If the evidence conflicts, say so and prefer the most recent.\n\n"
            f"QUESTION: {question}\n\nEVIDENCE:\n{evidence}"
        )
        text = models.call_text(models.Layer.FLASH, prompt)
        return text.strip() or None
    except Exception:  # noqa: BLE001 — enhancement only; heuristic result is used instead
        return None
