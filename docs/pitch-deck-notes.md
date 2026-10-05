# Pitch Deck Notes (slide-by-slide)

> Fill the prescribed template with this content. Keep it tight; the demo video
> carries the proof.

## Slide 1 — Title
- **TruthKeeper — the AI Knowledge Auditor**
- "Everyone built AI to answer from your documents. We built the AI that doesn't
  trust them — and proves which ones are wrong."
- Team name · AI Builder Cup 2026 · Future of Work & Enterprise Productivity.

## Slide 2 — Problem
- Enterprise knowledge bases rot: contradictions, stale pages, deprecated tools.
- Search + copilots **answer from** these docs → confidently repeat wrong info.
- No one audits the knowledge base itself. Cost: bad decisions, wasted time, risk.

## Slide 3 — Insight
- The valuable question isn't "what does this doc say?" but "**can I trust it?**"
- The hardest rot is **cross-document contradiction** — invisible to keyword search.

## Slide 4 — Solution
- TruthKeeper **interrogates** the knowledge base and produces a ranked,
  evidence-backed **Rot Report**: status + confidence + cited evidence + fix.
- Live demo "aha": a clean-looking deploy guide flagged *only* because it
  contradicts the CI/CD doc.

## Slide 5 — How it works (architecture)
- Firebase Hosting → Cloud Run (FastAPI) → Firestore cache → Gemini router.
- **Cache-first:** audit once, store in Firestore, serve cached → zero live
  model calls at eval time → free + flawless.
- Resilience ladder: Flash → Pro → Gemma → heuristic floor.

## Slide 6 — Google tech used
- **Gemini** (reasoning), **Firestore** (cache/data), **Cloud Run** (service),
  **Firebase** (hosting). 100% Google-family models.

## Slide 7 — Why it wins / differentiation
- Opposite of every "chat with your docs" entry.
- Catches contradictions keyword search can't.
- Evaluation-proof: works live, logged-out, instant, $0.

## Slide 8 — Cost & scale
- $0 target: always-free tiers + $300 credit; `min-instances=0`; cache every audit.
- Scales doc-by-doc; Pro escalation only for ambiguous docs.

## Slide 9 — What's next
- Live KB connectors (Drive, Confluence) via scheduled re-audits.
- Contradiction graph across the whole corpus; owner notifications; auto-PR fixes.

## Slide 10 — Close + links
- Live URL · GitHub repo · demo video.
- "The AI that doesn't trust your documents — and proves which ones are wrong."
