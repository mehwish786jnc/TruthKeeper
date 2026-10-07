"""Smart Context Optimization.

Selects only the relevant, non-redundant evidence to feed Gemini — trimming
tokens while preserving citations. Pure Python, no model calls, so it is free
and always available (even offline). Used by the audit prompt (for large
corpora), and by /ask and /research for retrieval.
"""

from __future__ import annotations

import re
from typing import Any

_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "of", "to", "in",
    "on", "for", "with", "as", "by", "at", "from", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its", "you",
    "your", "we", "our", "they", "their", "all", "any", "can", "will", "must",
    "should", "may", "not", "no", "do", "does", "how", "what", "when", "where",
    "which", "who", "into", "out", "up", "down", "over", "per", "via", "run",
    "use", "used", "using", "each", "only", "also", "within", "every",
}

_WORD = re.compile(r"[a-z0-9][a-z0-9\-\.]*")


def keywords(text: str) -> set[str]:
    """Lowercase keyword set, stopwords and short tokens removed."""
    return {w for w in _WORD.findall((text or "").lower()) if len(w) > 2 and w not in _STOP}


def _overlap(a: set[str], b: set[str]) -> float:
    """Jaccard similarity of two keyword sets."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / len(a | b)


def select_relevant(
    target: dict[str, Any],
    corpus: list[dict[str, Any]],
    *,
    max_docs: int = 10,
    min_score: float = 0.01,
) -> list[dict[str, Any]]:
    """Rank other docs by topical overlap with ``target``; drop near-duplicates.

    Returns the most relevant docs (those likely to confirm or contradict the
    target), capped at ``max_docs``. Preserves full doc dicts so citations and
    bodies stay intact.
    """
    tk = keywords(f"{target.get('title','')} {target.get('body','')}")
    scored: list[tuple[float, set[str], dict[str, Any]]] = []
    for d in corpus:
        if d["id"] == target["id"]:
            continue
        dk = keywords(f"{d.get('title','')} {d.get('body','')}")
        scored.append((_overlap(tk, dk), dk, d))
    scored.sort(key=lambda x: x[0], reverse=True)

    picked: list[dict[str, Any]] = []
    picked_keys: list[set[str]] = []
    for score, dk, d in scored:
        if score < min_score:
            break
        # dedupe: skip if ~identical to something already picked
        if any(_overlap(dk, pk) > 0.9 for pk in picked_keys):
            continue
        picked.append(d)
        picked_keys.append(dk)
        if len(picked) >= max_docs:
            break
    return picked


def rank_by_query(
    query: str,
    corpus: list[dict[str, Any]],
    *,
    max_docs: int = 5,
) -> list[dict[str, Any]]:
    """Return docs most relevant to a free-text query, best first (score > 0)."""
    qk = keywords(query)
    scored = []
    for d in corpus:
        s = len(qk & keywords(f"{d.get('title','')} {d.get('body','')}"))
        if s:
            scored.append((s, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:max_docs]]


def best_match(query: str, corpus: list[dict[str, Any]]) -> dict[str, Any] | None:
    ranked = rank_by_query(query, corpus, max_docs=1)
    return ranked[0] if ranked else None


def extractive_answer(doc: dict[str, Any], query: str, *, max_sentences: int = 2) -> str:
    """Pick the sentences from ``doc`` most relevant to the query (no model)."""
    body = doc.get("body", "")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    if not sentences:
        return body
    qk = keywords(query)
    ranked = sorted(sentences, key=lambda s: len(qk & keywords(s)), reverse=True)
    top = [s for s in ranked if qk & keywords(s)][:max_sentences]
    return " ".join(top) if top else " ".join(sentences[:max_sentences])


def trim(text: str, max_chars: int = 600) -> str:
    """Clip text to a token-ish budget, preserving the start (where claims live)."""
    text = text or ""
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"
