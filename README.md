# TruthKeeper — AI Knowledge Auditor

> Everyone built AI to answer from your documents.
> We built the AI that doesn't trust them — and proves which ones are wrong.

TruthKeeper **interrogates** a knowledge base instead of answering from it. It
detects **contradictions**, **stale content**, and **deprecated references**
across documents, then produces a ranked, evidence-backed **Rot Report** with
confidence scores and suggested fixes.

Built for the AI Builder Cup 2026 (Future of Work & Enterprise Productivity).

## Live URLs
- Frontend (Firebase Hosting): `TBD`
- Backend (Cloud Run): `TBD`

## Architecture (cache-first)
```
User ─► Firebase Hosting ─► Cloud Run (audit API) ─► Firestore cache
                                   │
                                   └─► model router ─► Gemini Flash / Pro / Gemma
```
Each document is audited **once**; results are cached in Firestore. The live app
**reads cached results**, so a judge's visit triggers **zero live model calls** —
free and dependency-free at evaluation time.

### Resilience ladder
`Firestore cache → Gemini Flash → Gemini Pro → Gemini free tier / Gemma → rule-based heuristics`

The heuristic floor guarantees the UI never shows a broken/empty screen.

## How the mandatory tech is used
| Tech       | Role                                                        |
|------------|-------------------------------------------------------------|
| Gemini     | Reasoning engine that detects contradictions/staleness      |
| Firestore  | Stores corpus + cached audit results (the cache-first core) |
| Cloud Run  | Hosts the FastAPI audit service (min-instances=0)           |
| Firebase   | Hosting for the Rot Report dashboard (+ Auth-ready)         |

## Local run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GCP_PROJECT, GCP_LOCATION, GEMINI_API_KEY
python smoke_test.py   # proves the planted contradiction is caught
uvicorn main:app --reload --port 8080
```
Then: `curl -X POST localhost:8080/audit` and `curl localhost:8080/report`.

## Deploy
```bash
# Backend
gcloud run deploy truthkeeper-api --source backend --region us-central1 \
  --allow-unauthenticated --min-instances=0 --max-instances=2 \
  --set-env-vars GCP_PROJECT=$GCP_PROJECT,GCP_LOCATION=us-central1 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest

# Frontend (set CLOUD_RUN_URL in frontend/config.js first)
firebase deploy --only hosting
```

## Repo layout
See `task.md` for the phase-by-phase build checklist and `plan.md` for the
full concept, stack, and constraints.
