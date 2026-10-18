# TruthKeeper — AI Knowledge Auditor

> Everyone built AI to answer from your documents.
> We built the AI that doesn't trust them — and proves which ones are wrong.

TruthKeeper **interrogates** a knowledge base instead of answering from it. It
detects **contradictions**, **stale content**, and **deprecated references**
across documents, then produces a ranked, evidence-backed **Rot Report** with
confidence (trust) scores — and closes the loop with AI-drafted, human-approved
fixes that are re-audited.

Built for the AI Builder Cup 2026 (Future of Work & Enterprise Productivity).

## Live URLs
- **App (Firebase Hosting):** https://truthkeeper-2631.web.app
- **API (Cloud Run):** https://truthkeeper-api-815359665978.us-central1.run.app

## What it does
- **Automated audit** — classifies every document as `healthy` / `contradictory`
  / `stale` / `deprecated`, with evidence and a trust score.
- **Trust-gated Q&A** — answers are gated on the source's trust; conflicting or
  unreliable sources are flagged/withheld instead of guessed.
- **Deep research** — compares conflicting documents and recommends a decision.
- **Knowledge graph** — derives contradiction / reference / dependency edges and
  surfaces conflict clusters, hubs, and at-risk documents.
- **Impact analysis** — shows the documents, teams, and processes a change affects.
- **AI remediation** — `propose-fix` drafts a correction (no save) → human approves
  the diff → `apply-fix` saves, re-audits the doc and the ones it conflicted with.
- **Decision log** — every approve/dismiss is persisted for an audit trail.

## Architecture (cache-first)
```
User ─► Firebase Hosting (static SPA) ─► Cloud Run (FastAPI audit API) ─► Firestore
                                                 │
                                                 └─► model router ─► Vertex AI
                                                      Gemini 2.5 Flash / Pro / Gemma 3
```
Each document is audited **once**; results are cached in Firestore. The live app
**reads cached results** (`GET /report`), so a judge's visit triggers **zero live
model calls** — fast and near-$0 at evaluation time. The AI layer runs only on a
cache miss (a new or re-audited document).

### Resilience ladder
`Firestore cache → Gemini 2.5 Flash → Gemini 2.5 Pro → Gemma 3 27B → rule-based heuristics`

The heuristic floor guarantees the UI never shows a broken/empty screen.

## Tech stack
| Tech        | Role                                                            |
|-------------|-----------------------------------------------------------------|
| Vertex AI   | Gemini 2.5 Flash/Pro + Gemma 3 — detects contradictions/staleness |
| Firestore   | Corpus + cached audits/decisions/insights (the cache-first core) |
| Cloud Run   | Hosts the FastAPI audit service (scale-to-zero, min-instances=0) |
| Firebase    | Hosting for the dashboard (vanilla HTML/CSS/JS, no build step)   |
| FastAPI     | Python 3.11 API (Pydantic validation); `pypdf` for PDF ingestion |

## Local run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set GCP_PROJECT, GCP_LOCATION (GEMINI_API_KEY optional)
python smoke_test.py   # proves the planted contradiction is caught
uvicorn main:app --reload --port 8080
```
Then: `curl -X POST localhost:8080/audit` and `curl localhost:8080/report`.

For the frontend, point `frontend/config.js` `CLOUD_RUN_URL` at your backend
(e.g. `http://localhost:8080`) and serve the `frontend/` folder statically.

## Deploy
```bash
# Backend (Vertex AI path — uses application-default / runtime service account)
gcloud run deploy truthkeeper-api --source backend --region us-central1 \
  --allow-unauthenticated --min-instances=0 --max-instances=2 \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,GCP_LOCATION=us-central1

# Frontend (set CLOUD_RUN_URL in frontend/config.js first)
firebase deploy --only hosting
```
> The `GEMINI_API_KEY` (AI Studio) is only needed for the Gemma fallback layer;
> the primary path uses Vertex AI via the Cloud Run service account, so no secret
> is required for a standard deploy.

## Key API endpoints
```
GET    /report                     cached audits, worst-first (zero model calls)
GET    /documents                  the live corpus
POST   /documents                  upload text or PDF -> save -> audit
DELETE /documents/{id}             remove a document + its audit
POST   /documents/{id}/audit       re-audit one document
POST   /documents/{id}/propose-fix AI drafts a correction (does NOT save)
POST   /documents/{id}/apply-fix   save human-approved fix -> re-audit + cascade
GET    /graph /health-score /insights /verify
POST   /ask /research /impact /decisions
```

## Repo layout
```
backend/    FastAPI service (audit engine, insights, Firestore store, seed corpus)
frontend/   Static single-page app (served by Firebase Hosting)
docs/        architecture.md, gcp-setup.md
logs.md      day-by-day build journal
```
See [`docs/architecture.md`](docs/architecture.md) for design detail,
[`docs/gcp-setup.md`](docs/gcp-setup.md) for the full cloud setup, and
[`API_CONTRACT.md`](API_CONTRACT.md) for the request/response shapes.
