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

## Day 5 — 2026-10-17 · Live on GCP (backend + frontend deployed)
- **GCP project set up** on `truthkeeper-2631` (project number 815359665978, account meenusa2003@gmail.com, free trial active). Logged in `gcloud` (CLI + application-default) and `firebase`.
- **Enabled APIs**: Cloud Run, Vertex AI (`aiplatform`), Firestore, Cloud Build, Artifact Registry, Secret Manager, plus Firebase + Firebase Hosting.
- **Firestore** database created (Native mode, us-central1, free-tier).
- **IAM**: granted the Cloud Run runtime service account (`815359665978-compute@developer.gserviceaccount.com`) `roles/aiplatform.user`, `roles/datastore.user`, and `roles/cloudbuild.builds.builder` (needed for source-based deploys).
- **First live audit**: ran `smoke_test.py` against real Gemini Flash + Firestore — all 15 docs audited and cached; planted findings caught (deployment-guide↔cicd-pipeline and password-policy↔security-standards-2025 contradictory, monitoring/vpn deprecated, database-backup stale). One doc (expense-policy) fell back to heuristic on a transient model hiccup.
- **Backend deployed to Cloud Run** (public, scale-to-zero, max 2, 512Mi): https://truthkeeper-api-815359665978.us-central1.run.app . Verified `/report`, `/verify`, `/graph`, `/health-score` serve cached results live.
- **Firebase added** to the existing GCP project; **frontend deployed to Firebase Hosting**: https://truthkeeper-2631.web.app . Pointed `frontend/config.js` `CLOUD_RUN_URL` at the Cloud Run backend; fixed `.firebaserc` to `truthkeeper-2631`. CORS from the hosted site to the backend confirmed working.
- Known cosmetic: backend `/healthz` returns a Google edge 404, so the Settings "test connection" indicator shows false "unhealthy"; the app uses `GET /report` and works. Not yet done: $5 budget alert.

## Day 6 — 2026-10-17 · Fully dynamic — everything served from the backend
Goal: remove hardcoded data; when online, every piece comes from the backend (sample-data.js kept only as the offline fallback).

**Backend**
- `store.py`: added a `documents` collection (get/save/get_all/delete) and an `insights` collection (get/save), plus `delete_audit`, mirroring the existing audits/decisions pattern. Documents store their `id` inside the payload.
- `main.py`: added `get_corpus()` (Firestore-first, on-disk `seed/corpus.json` fallback) and routed the 7 corpus-reading handlers through it. New endpoints: `GET /documents`, `POST /documents` (text or PDF upload → save → audit the new doc), `DELETE /documents/{id}` (removes doc + its audit), `POST /documents/{id}/audit` (re-audit one), `GET /insights`. Startup event seeds `documents` from `seed/corpus.json` + `seed/owners.json` if empty (preserves uploads), and always refreshes `insights` from `seed/insights.json` (authored content, repo = source of truth).
- PDF upload extracts text with `pypdf`; added `pypdf` + `python-multipart` to `requirements.txt`. New seeds: `seed/owners.json` (team/POC per doc, lifted from build_pdfs OWNERS) and `seed/insights.json` (gaps, processes, non-contradiction relationships, research, impact, remediation, history — extracted from the old `sample-data.js` DEMO).
- Verified locally against real Firestore + Gemini: list/upload(text & PDF)/delete round-trips work; seeded 15 docs + insights into prod Firestore.

**Frontend (`app.js`)**
- Rewrote `loadData()`: when a backend URL is set, fetch `/report`, `/documents`, `/health-score`, `/graph`, `/decisions`, `/insights` in parallel and assemble `STATE.corpus`/`STATE.audits`/`STATE.demo` in the **same shapes** `sample-data.js` used (via new `buildDemoFromBackend` + `fetchJSON` helpers), so the ~17 render functions are unchanged. `teams` derived from each doc's `owner.team`; `health` mapped from `/health-score`; graph contradiction edges merged with authored relationships; `decisionLog` from `/decisions`. On any failure → offline demo fallback (unchanged), and the localStorage user-docs merge is now offline-only.
- Upload/delete/re-audit now hit the backend when online: `submitDoc` → `POST /documents` (multipart, supports `.pdf`), `deleteUserDoc` → `DELETE /documents/{id}`, drawer re-audit → `POST /documents/{id}/audit`; each refreshes via `loadData()`. `renderManageList` allows delete for all docs when online. Widened the upload dropzone to accept PDFs (server-side extraction). Fixed the Settings "test connection" to probe `GET /report` instead of `/healthz`.

**Deploy & verify**
- Redeployed backend (Cloud Run revision 00002) and frontend (Firebase Hosting). Confirmed live: `/documents` (15, with owner), `/insights` (7 keys), `/health-score`, `/graph`; and a production upload→list(16)→delete(15) round-trip with a live Gemini audit. Changes are in the working tree (not yet committed).

## Day 7 — 2026-10-18 · Interactive tools go live + enriched (no more prefab)
An app-wide audit found the interactive tools still ran on seeded/prefab content or client-local state even when online. Wired them to the real endpoints and enriched the backend so they stay rich.

**Backend (`insights.py`)**
- `research()` now returns the shape the research view renders directly: `{q, recommendation, decision, based_on, confidence, sources, evidence, contradictions, gaps, comparison}`. `recommendation`+`decision`+`comparison` come from a single **structured Gemini JSON call** (`_gemini_research`) grounded only in the retrieved docs; heuristic/extractive fallback (and `comparison:null`) on any model failure. Verified: a conflicting question yields a live 5-row comparison table.
- `impact()` now returns `{risk, affectedDocs:[{id,reason}], processes, teams, actions}` — derived live from audit contradictions + topical neighbours, `processes` from `/insights`, `teams` from each doc's `owner`, status-templated `actions`. No model (fast/free).
- `/ask`, `/decisions` unchanged (already existed).

**Frontend (`app.js`)**
- Deep Research `research()` → `POST /research` when online (prefab path kept offline). Impact `showImpact()` → `POST /impact`. Quick Ask `ask()` → `POST /ask` (renderAnswer now accepts the server result: source + trust + answer, conflict block still from the live audit).
- New `recordDecision()` persists via `POST /decisions` (optimistic local + backend write); wired into research "Record decision", remediation Approve (`approveRemediation`) and Dismiss. Decisions now survive a reload.

**Deploy & verify**
- Backend Cloud Run revision 00003 + frontend redeploy. Verified live: `/research` returns a real Gemini comparison (sources password-policy↔security-standards-2025, 5-row table, decision "Do not enforce 90-day password rotation"); `/impact` returns live risk/affected/teams; and a `POST /decisions` → `GET /decisions` round-trip persisted (then cleaned up). Deployed `app.js` confirmed to contain the new wiring. Working tree still uncommitted.
- Left cosmetic items as-is per owner: synthetic health trend, doc version-history timeline, quick-ask suggestion chips, Run-Audit progress labels.

## Day 8 — 2026-10-18 · Correctness + "smart" passes (LOCAL, not yet deployed)
A series of local-only refinements (owner asked to hold deploys). All verified against the live Firestore/Gemini locally; **working tree not committed, not deployed.**

- **Bug fix — audit parse:** Gemini returns `suggested_fix: null` for healthy docs, which failed Pydantic validation and silently dropped the doc to the heuristic floor. `audit._parse` now drops null fields (and null keys in contradictions) so model results validate. (This was why `expense-policy` showed `heuristic`.)
- **Ask output polish:** fixed answer/evidence duplication (Evidence now shows real audit quotes), added a confidence figure to the trust banner, clearer withheld state, and the research confidence is now the animated ring.
- **Updated · Owner · POC everywhere:** `poc` was stored but never shown; added `ownerTeamOf`/`pocOf` and surfaced all three in the doc drawer, Knowledge table, Ask source line, and impact inspector.
- **Add & Manage fixes:** upload form now captures **POC** and honors the chosen **Last updated** date (`POST /documents` gained `poc`/`last_updated`); manage rows show updated·owner·POC + a per-row Re-audit; offline path stores `owner` as `{team, poc}` for consistency.
- **Dynamic graph connections:** `insights.build_graph` now derives all edges live — contradictions (audits) + references (doc names/titles) + dependency (filtered shared-topic overlap) — replacing the seeded relationship list. Honest/sparse: for the seed corpus it yields contradictions + 1 reference (no fabricated topical links).
- **Graph Insights panel:** Knowledge Graph now shows graph-only analytics — conflict clusters, most-connected hub, at-risk healthy docs (adjacent to a conflict), isolated docs — all computed live and clickable.
- **Targeted cross-doc re-audit:** uploading/re-auditing a doc now also re-audits just the docs it contradicts (not the whole corpus), so a new conflict shows on both sides. Verified both sides flip.
- **AI remediation (preview → approve → apply):** new `POST /documents/{id}/propose-fix` (Gemini drafts a corrected body, does NOT save) and `POST /documents/{id}/apply-fix` (saves the human-approved body, re-audits the doc + its former counterparts). The remediation stepper shows the real before/after diff for human approval. Honest: the re-audit reports the live verdict (no faked "healthy"); the approved rewrite is persisted regardless.
- Pending deploy (backend + frontend) whenever the owner approves.

## Day 9 — 2026-10-18 · Deployed Day 8 work + removed stray demo decision
- **Fix:** removed the one hardcoded decision-log entry ("Confirmed 7-year retention is current", data-retention) that lived in `frontend/sample-data.js` and surfaced on the live site even though the real backend log was empty. `decisionLog` is now `[]` — the log starts empty and only fills with real decisions (online from `/decisions`, offline from local actions).
- **Deployed** all Day 8 backend changes to Cloud Run (**revision 00005**, env `GCP_PROJECT`/`GCP_LOCATION`, Vertex AI path — no Gemini secret, matching the prior working config) and the frontend to Firebase Hosting.
- **Verified live:** backend `/report` 15 docs, `/decisions` empty `{}`, `/graph` typed edges `{contradiction:4, reference:1}` (dynamic graph), `/insights` 7 keys; deployed `sample-data.js` shows `decisionLog: []`. Live site: https://truthkeeper-2631.web.app , backend https://truthkeeper-api-815359665978.us-central1.run.app .

