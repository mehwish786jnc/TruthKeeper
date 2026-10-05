"""Local smoke test: prove TruthKeeper catches the planted contradiction.

Audits the seed corpus and asserts that `deployment-guide` is flagged as
contradictory against `cicd-pipeline`. Requires a configured .env (GCP_PROJECT,
GCP_LOCATION, GEMINI_API_KEY) and Firestore access.

Run:  python smoke_test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import audit

CORPUS_PATH = Path(__file__).parent / "seed" / "corpus.json"


def main() -> int:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(corpus)} docs. Auditing (force=True)...\n")

    results = audit.audit_corpus(corpus, force=True)

    for r in results:
        flags = ""
        if r.contradictions:
            flags = " vs " + ", ".join(c.other_doc for c in r.contradictions)
        print(f"  {r.confidence:0.2f}  {r.status:<13} {r.doc_id}{flags}  [{r.model_used}]")

    target = next((r for r in results if r.doc_id == "deployment-guide"), None)
    if target is None:
        print("\nFAIL: deployment-guide not found in results")
        return 1

    contradicts_cicd = any(
        c.other_doc == "cicd-pipeline" for c in target.contradictions
    )
    ok = target.status == "contradictory" and contradicts_cicd

    print()
    if ok:
        print("PASS: deployment-guide flagged contradictory vs cicd-pipeline, cached in Firestore.")
        return 0
    print(f"FAIL: expected contradictory vs cicd-pipeline, got status={target.status}, "
          f"contradictions={[c.other_doc for c in target.contradictions]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
