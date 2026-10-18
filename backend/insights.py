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
    """Nodes = documents (health-colored); edges derived live from the corpus:
    contradictions (from audits), references (one doc names another), and
    dependencies (strong shared-topic overlap)."""
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

    def _add(a_id: str, b_id: str, etype: str, explanation: str, evidence: str = "") -> None:
        if not a_id or not b_id or a_id == b_id:
            return
        key = tuple(sorted([a_id, b_id]))
        if key in seen:
            return
        seen.add(key)
        edges.append({"a": a_id, "b": b_id, "type": etype, "explanation": explanation, "evidence": evidence})

    # 1) Contradictions — live, strongest signal (added first so they win the dedup).
    for a in audits.values():
        for c in a.get("contradictions", []) or []:
            _add(a["doc_id"], c.get("other_doc", ""), "contradiction",
                 c.get("explanation", ""), c.get("evidence", ""))

    # 2) References — one document explicitly names another (by id or full title).
    for d in corpus:
        body_lc = (d.get("body") or "").lower()
        for o in corpus:
            if o["id"] == d["id"]:
                continue
            title_lc = (o.get("title") or "").lower()
            if o["id"].lower() in body_lc or (len(title_lc) >= 6 and title_lc in body_lc):
                _add(d["id"], o["id"], "reference",
                     f"“{d.get('title', d['id'])}” references “{o.get('title', o['id'])}”.")

    # 3) Dependencies — meaningful shared-topic overlap (derived; filtered to limit noise).
    _STOP = {"after", "never", "their", "there", "which", "would", "could", "should",
             "these", "those", "other", "about", "where", "while", "being", "during",
             "every", "always", "please", "within", "using", "guide", "document"}

    def _topics(text: str) -> set[str]:
        return {w for w in context.keywords(text) if len(w) >= 5 and w.isalpha() and w not in _STOP}

    for d in corpus:
        d_topics = _topics(f"{d.get('title', '')} {d.get('body', '')}")
        for o in context.select_relevant(d, corpus, max_docs=2):
            shared = sorted(d_topics & _topics(f"{o.get('title', '')} {o.get('body', '')}"))
            if len(shared) >= 3:
                _add(d["id"], o["id"], "dependency", "Shares subject matter: " + ", ".join(shared[:5]))

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
    contradictions and gaps, and recommend an action — returned in the shape the
    dashboard's research view renders directly."""
    docs = context.rank_by_query(question, corpus, max_docs=5)
    if not docs:
        return {"q": question, "recommendation": "No relevant knowledge found for this question.",
                "decision": None, "based_on": None, "confidence": 0.0,
                "sources": [], "evidence": [], "contradictions": [],
                "gaps": ["No matching documents."], "comparison": None}
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

    sources = [{
        "id": d["id"],
        "status": audits.get(d["id"], {}).get("status", "uncertain"),
        "conf": audits.get(d["id"], {}).get("confidence", 0.5),
    } for d in docs]
    evidence = [{"doc": d["id"], "text": context.extractive_answer(d, question, max_sentences=1)} for d in docs[:3]]
    confidence = round(sum(s["conf"] for s in sources) / len(sources), 2)

    gaps = []
    if not trusted:
        gaps.append("No fully-trusted source matched — recommendation is provisional and needs review.")
    if contradictions:
        gaps.append("Sources disagree; the newer/authoritative document should supersede.")

    gen = _gemini_research(question, docs, audits)
    if gen:
        recommendation = gen.get("recommendation") or context.extractive_answer(base, question, max_sentences=3)
        decision = gen.get("decision") or None
        comparison = gen.get("comparison") or None
    else:
        recommendation = context.extractive_answer(base, question, max_sentences=3)
        decision = None
        comparison = None

    return {
        "q": question,
        "recommendation": recommendation,
        "decision": decision,
        "based_on": base["id"],
        "confidence": confidence,
        "sources": sources,
        "evidence": evidence,
        "contradictions": contradictions,
        "gaps": gaps,
        "comparison": comparison,
    }


# --------------------------------------------------------------------------- #
# ACT: impact / remediate
# --------------------------------------------------------------------------- #
def _teams_of_doc(doc: dict[str, Any] | None) -> list[str]:
    owner = (doc or {}).get("owner", {})
    team = owner.get("team") if isinstance(owner, dict) else owner
    return [t.strip() for t in str(team or "").split(",") if t.strip()]


def impact(doc_id: str, corpus: list[dict[str, Any]]) -> dict[str, Any]:
    """Impact Analysis: what's affected if this document changes — returned in the
    shape the dashboard's impact tool renders directly."""
    target = _doc(corpus, doc_id)
    if not target:
        return {"doc_id": doc_id, "found": False, "risk": "low",
                "affectedDocs": [], "processes": [], "teams": [], "actions": []}
    audits = _audits_by_id()
    affected: dict[str, str] = {}

    # 1) direct contradiction links (strongest signal), then reverse links
    for c in audits.get(doc_id, {}).get("contradictions", []) or []:
        other = c.get("other_doc")
        if other and other != doc_id:
            affected[other] = c.get("explanation", "Directly conflicts with this document.")
    for a in audits.values():
        for c in a.get("contradictions", []) or []:
            if c.get("other_doc") == doc_id and a["doc_id"] != doc_id and a["doc_id"] not in affected:
                affected[a["doc_id"]] = "References or conflicts with this document."

    # 2) topical neighbours (shared subject matter → likely need review)
    for d in context.select_relevant(target, corpus, max_docs=6):
        if d["id"] != doc_id and d["id"] not in affected:
            shared = sorted(context.keywords(f"{target.get('title', '')} {target.get('body', '')}")
                            & context.keywords(f"{d.get('title', '')} {d.get('body', '')}"))[:5]
            if shared:
                affected[d["id"]] = "Shares subject matter: " + ", ".join(shared)

    affected_docs = [{"id": k, "reason": v} for k, v in affected.items()]

    # processes this doc participates in (authored insights)
    processes = []
    try:
        for p in (store.get_insights() or {}).get("processes", []) or []:
            if doc_id in (p.get("docs") or []):
                processes.append({"name": p.get("name"), "status": p.get("status")})
    except Exception:  # noqa: BLE001 - insights optional
        pass

    # owner teams across the doc + everything it affects
    teams: list[str] = []
    for did in [doc_id, *affected.keys()]:
        for t in _teams_of_doc(_doc(corpus, did)):
            if t not in teams:
                teams.append(t)

    status = audits.get(doc_id, {}).get("status", "uncertain")
    risk = "high" if status == "contradictory" else "low" if status == "healthy" else "medium"

    if status == "contradictory":
        actions = ["Reconcile this document with the conflicting source",
                   "Confirm which source is authoritative (usually the more recent)",
                   "Notify the owner teams", "Re-audit after the change"]
    elif status == "deprecated":
        actions = ["Replace the deprecated tools/references",
                   "Update linked documents that assume the old tooling",
                   "Notify the owner teams", "Re-audit after the change"]
    elif status == "stale":
        actions = ["Review and refresh the content", "Update the last-reviewed date",
                   "Re-audit after the change"]
    else:
        actions = ["Review affected documents", "Notify owner teams", "Re-audit after the change"]

    return {"doc_id": doc_id, "found": True, "title": target.get("title"),
            "risk": risk, "affectedDocs": affected_docs, "processes": processes,
            "teams": teams, "actions": actions}


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
# optional Gemini enrichment for research (never required; fails to heuristic)
# --------------------------------------------------------------------------- #
def _gemini_research(
    question: str, docs: list[dict[str, Any]], audits: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Ask Gemini for a structured research payload (recommendation + decision +
    optional A/B comparison) grounded ONLY in the retrieved docs. Returns a dict
    or None on any failure, so research() always has a heuristic floor."""
    try:
        import json as _json
        import models  # local import so offline/import issues never break the endpoint

        srcs = []
        for d in docs:
            st = audits.get(d["id"], {}).get("status", "uncertain")
            srcs.append(f"[{d['id']}] (status={st}, updated {d.get('last_updated', '?')}) "
                        f"{d.get('title', '')}\n{context.trim(d.get('body', ''), 500)}")
        prompt = (
            "You are TruthKeeper's research assistant. Using ONLY the sources below, answer the "
            "QUESTION. Return STRICT JSON matching exactly:\n"
            '{"recommendation": "2-4 sentences citing [doc-ids]", '
            '"decision": "short imperative label, <= 8 words", '
            '"comparison": {"title": "...", "a": "outdated/rejected option", '
            '"b": "recommended option", "rows": [{"dim": "aspect", "a": "...", "b": "..."}]}}\n'
            "Rules: ground everything in the sources only; prefer the more recent / healthy source. "
            "If two sources conflict, the comparison must contrast them with 3-5 rows (a = the "
            "outdated one, b = recommended). If there is no meaningful A-vs-B choice, set "
            '"comparison" to null. Return ONLY the JSON object.\n\n'
            f"QUESTION: {question}\n\nSOURCES:\n" + "\n\n".join(srcs)
        )
        data = _json.loads(models.call_model(models.Layer.FLASH, prompt))
        if not isinstance(data, dict):
            return None
        comp = data.get("comparison")
        if not (isinstance(comp, dict) and isinstance(comp.get("rows"), list) and comp.get("rows")):
            data["comparison"] = None
        return data
    except Exception:  # noqa: BLE001 — enrichment only; heuristic result is used instead
        return None


def rewrite_to_resolve(
    doc: dict[str, Any], audit_record: dict[str, Any], corpus: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Use the model to rewrite a flagged document's body so the issue is resolved —
    contradictions reconciled against the authoritative source, deprecated references
    replaced, stale content refreshed. Returns ``{"revised_body", "change_summary"}``
    or ``None`` if a fix can't be generated (caller then falls back to manual)."""
    try:
        import json as _json
        import models

        status = (audit_record or {}).get("status", "uncertain")
        suggested = (audit_record or {}).get("suggested_fix", "")
        evidence = (audit_record or {}).get("evidence", []) or []
        evidence_text = "\n".join(f"- {e}" for e in evidence) if evidence else "(none listed)"
        by_id = {d["id"]: d for d in corpus}
        conflicts = []
        for c in (audit_record or {}).get("contradictions", []) or []:
            o = by_id.get(c.get("other_doc", ""))
            if o:
                conflicts.append(f"[{o['id']}] (updated {o.get('last_updated', '?')})\n"
                                 f"{context.trim(o.get('body', ''), 600)}")
        conflict_text = "\n\n".join(conflicts) if conflicts else "(no conflicting document)"

        prompt = (
            "You are TruthKeeper's remediation assistant. Rewrite the DOCUMENT below so that it would "
            f"pass a fresh audit as HEALTHY. It is currently flagged '{status}'.\n"
            f"Audit guidance: {suggested or 'correct the flagged issue'}.\n"
            "Resolve EVERY issue, not just one:\n"
            "- Reconcile any contradiction by updating THIS document to AGREE with the more recent / "
            "authoritative source under CONFLICTS.\n"
            "- Replace EVERY deprecated/retired tool or reference flagged under ISSUES with its current "
            "equivalent (do not leave the old name anywhere in the text).\n"
            "- Refresh stale instructions.\n"
            "Preserve everything still correct, keep the original structure, headings and tone, and "
            "introduce no facts beyond the provided sources. "
            'Return STRICT JSON: {"revised_body": "<the full corrected document body>", '
            '"change_summary": "<1-2 sentences on what changed>"}.\n\n'
            f"DOCUMENT [{doc['id']}] {doc.get('title', '')} (updated {doc.get('last_updated', '?')}):\n"
            f"{doc.get('body', '')}\n\nISSUES (flagged evidence):\n{evidence_text}\n\nCONFLICTS:\n{conflict_text}"
        )
        data = _json.loads(models.call_model(models.Layer.FLASH, prompt))
        if isinstance(data, dict) and isinstance(data.get("revised_body"), str) and data["revised_body"].strip():
            return {"revised_body": data["revised_body"].strip(),
                    "change_summary": (data.get("change_summary") or "").strip()}
        return None
    except Exception:  # noqa: BLE001 — fix generation is best-effort; caller falls back to manual
        return None
