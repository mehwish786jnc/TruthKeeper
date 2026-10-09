# TruthKeeper — Work Log

A day-by-day journal of what's been built and decided, from day 1.
Chronological: oldest at the top, newest appended at the bottom.

> Convention: append a new dated section at the bottom for each notable change set.
> Keep it factual — what was actually done, not plans. Plans live in `plan.md` / `task.md`.
> Dates are anchored to git commit history where possible.

---

## Day 1 — 2026-10-05 · Project scaffold
*Commits: `b5f4471`, `c1fd5c0`, `a6cd0ef`*

- Scaffolded the TruthKeeper MVP: concept = an **AI Knowledge Auditor** that interrogates a knowledge base for contradictions, stale content, and deprecated references, producing a ranked "Rot Report."
- **Backend audit engine** (FastAPI): initial routing ladder (Firestore cache → Gemini Flash → Pro → Gemma → heuristic floor), `AuditResult` contract, deprecated-term detection.
- **Seed corpus**: "Northwind" documents with planted findings so the audit always has something real to catch.
- Initial **frontend** (single page) + project docs (`plan.md`, `task.md`).
- Set up the GitHub repo: https://github.com/mehwish786jnc/TruthKeeper.git
- Removed `.github/copilot-instructions.md`; updated `task.md` with completed phases.
- **Standing constraints locked in**: Google/GCP models only in the product path; cache-first; target $0; must work live / logged-out / offline (evaluation-proof); secrets only via env / Secret Manager, never committed.

## Day 2 — 2026-10-06 · Full product + animated frontend
*Commit: `18596b0`*

- Reframed from "one page" into a **full enterprise product**: app shell with sidebar nav grouped UNDERSTAND → TRUST → DECIDE → ACT, multiple views, per-doc drawer with tabs, remediation stepper, impact tool, decision log.
- **Backend API expanded**: `/graph`, `/verify`, `/health-score`, `/decisions` (GET+POST), `/ask`, `/research`, `/impact`, `/remediate` — all model-optional with heuristic fallbacks. Cache-first default path (`GET /report`) makes zero model calls.
- **Northwind corpus** finalized to 15 docs with concrete planted findings (deployment-guide ⟷ cicd-pipeline contradiction, password-policy ⟷ security-standards conflict, deprecated monitoring, stale vpn/backup docs); 2026-dated.
- **Demo-data-driven frontend** (`sample-data.js`) so the whole product works offline with graceful fallback to demo data.
- Added **API contract** and **MVP plan** docs.
- Design iteration: experimented with animated canvas backgrounds (galaxy / particles).

## Day 3 — 2026-10-07 · Design overhaul, landing page, UX consolidation
*Commit: `57dfae4` (pushed to origin/main)*

- **Design direction settled** after several rejected iterations (plain stars, heavy particle web, framed tubes-in-a-box): landed on the **"Futuristic Precision" cyber theme** — #050505 base, cyan/violet/emerald neon, glassmorphism, Syncopate (display) + Space Grotesk (body), uppercase labels, neon conic buttons. Unified across app **and** landing. Uniform outline SVG icons sitewide.
- **Landing page** (`landing.html/.css/.js`): scroll-driven effects (progress bar, parallax, reveals, pinned scrollytelling, horizontal scroll, count-ups, scroll-driven color wash) + the light-bleeding **tubes cursor** (`tubes.js`, three.js via CDN with offline fallback).
- **Alignment / typography fixes** at the shared-component level: generalized the `h4` section-label style across cards/answers/research/graph-inspector/drawer/fix (was only styled inside `.card`); added the missing `.card-acts` rule; gave `.fix` a `--c` color fallback so fix boxes render outside cards; deduplicated `.brand-name` / `.tb-title h1`.
- Knowledge → Documents table: applied a 5-column reorder to fix a Trust-column wrap, then **reverted** it at user request — back to `Document · Updated · Owner · Status · Trust`.
- **Merged Ask AI + Research** into one **Ask** view with a Quick answer / Deep research mode toggle (each mode self-describes at point of use). Removed the separate Research nav/route; legacy `#/research` → Ask in Deep mode. *Reason: two near-identical search boxes was confusing UX.*
- **Home nav item** added at top of sidebar → links back to `landing.html`.
- **Add Documents view** (new, under TRUST): upload `.txt`/`.md` (drag-drop or picker) or paste; metadata form; client-side `heuristicAudit` (flags deprecated tooling / stale dates / too-short content); persisted to `localStorage`; manage list with open/delete of user-added docs. Added docs flow into Knowledge, Graph, and Ask. Seed corpus copied (`.slice()`) so deletes never mutate it.
- Added backend `insights.py` / `context.py` (Smart Context Optimization).
- Committed + pushed everything to `origin/main`. No secrets committed (`.env*` gitignored; only `.env.example` tracked).

## Day 4 — 2026-10-09 · Strategy, deploy review, logging
- **Hackathon track review** — assessed TruthKeeper against "Future of Work & Enterprise Productivity." Verdict: strong fit (document intelligence + knowledge assistant + research assistant + decision/workflow), differentiated by the **trust/verification** angle vs. plain RAG search. Gap identified: named GCP services not yet used (**Vertex AI Search**, **Document AI**, **Agent Engine/ADK**); recommended adding Vertex AI Search (retrieval) and Document AI (upload ingestion) behind the offline fallback. *(Not yet implemented.)*
- **GCP deploy feasibility** confirmed: all artifacts present (`Dockerfile`, `requirements.txt`, `.dockerignore`, `firebase.json`, `.firebaserc`) → config-only deploy, no rebuild. Mapping: frontend → Firebase Hosting, backend → Cloud Run, data → Firestore, models → Vertex AI (+ AI Studio/Gemma fallback), secrets → Secret Manager.
- **Cost analysis**: ~$0 actual spend at demo scale (cache-first → zero model calls on the render path; free tiers for Cloud Run / Firestore / Hosting). Asterisk: Vertex AI requires a billing account to exist; AI Studio key / heuristic floor avoids that entirely.
- Created this **`logs.md`** work log.

### Physical documents + task.md refresh
- **Built the 15 knowledge-base docs as real PDFs** (`backend/seed/pdfs/*.pdf`), ~6 pages each. Authored long-form wiki/runbook/policy content in `backend/seed/content.py` (`LONG_BODIES` + an `APPENDIX` of extra sections for the shorter docs) and render it with `backend/seed/build_pdfs.py` (reportlab, build-time only). All planted findings preserved verbatim; `pypdf` extraction confirms them. Fixed a renderer bug where each source line became its own paragraph (prose now flows). Regenerate: from `backend/`, `python -m seed.build_pdfs`.
- **Rewrote `task.md`** to reflect reality: backend + frontend + 15 PDFs done; next = ingest PDFs into a Firestore `documents` collection and make the app dynamic (Document AI + pypdf fallback), then GCP deploy and submission assets.

