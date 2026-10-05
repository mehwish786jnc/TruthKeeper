# Demo Script (≤ 4:00) — against the LIVE URL

> Goal: land the "aha" — a doc that *looks* fine is flagged because it
> **contradicts another doc**, something keyword search would never catch.

## 0:00–0:30 — The problem
"Every enterprise has a knowledge base full of docs that quietly rot:
contradictions, stale pages, deprecated tools. Search and copilots happily
*answer from* those rotten docs — and confidently repeat the wrong thing.
TruthKeeper does the opposite: it **interrogates** the knowledge base and tells
you which docs you can't trust."

## 0:30–1:00 — The corpus
- Open the live Firebase URL (incognito / logged-out).
- "Here's a 15-document knowledge base — engineering, security, ops, finance."
- Point out the summary tiles: X docs audited, Y flagged.

## 1:00–2:30 — The Rot Report (worst-first)
- Scroll the ranked report. Start at the top (lowest confidence).
- **The aha:** open `deployment-guide`.
  - "This doc looks totally reasonable on its own — deploy with `deploy.sh` to Heroku."
  - "But TruthKeeper flagged it **contradictory** — because `cicd-pipeline` says
    deploys are fully automated through GitHub Actions to Cloud Run, and that
    'there is no Heroku in our stack.'"
  - Show the cited evidence from *both* docs. "Keyword search would never catch this."
- Quickly show the other planted findings:
  - `password-policy` vs `security-handbook` (90-day rotation vs no rotation).
  - `monitoring-setup` — **deprecated** (Stackdriver/Nagios).
  - `vpn-access`, `db-backup` — **stale** (2021).

## 2:30–3:15 — How it works (cache-first)
- "Every audit is powered by **Gemini**, cached in **Firestore**, served from
  **Cloud Run**, and fronted by **Firebase Hosting**."
- "The page you're looking at made **zero live model calls** — it reads cached
  results. That's why it's instant, free, and can't break during judging."
- Mention the resilience ladder: Flash → Pro → Gemma → heuristic floor.

## 3:15–3:45 — Suggested fixes + confidence
- "Each finding comes with cited evidence, a confidence score, and a suggested
  fix — so a knowledge owner can act immediately."

## 3:45–4:00 — Close
"TruthKeeper: the AI that doesn't trust your documents — and proves which ones
are wrong. Built entirely on Google Cloud, at $0."

## Pre-demo checklist
- [ ] `POST /audit` pre-run so Firestore is fully populated.
- [ ] Load the live URL in incognito; confirm < 3s render, no errors.
- [ ] Confirm `deployment-guide` is near the top and shows the contradiction.
