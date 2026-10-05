# TASK.md — TruthKeeper MVP (0 → deployed)

> Agent: execute these phases **in order**. Do not skip ahead. After each phase,
> run its **Acceptance check** and only continue if it passes. Follow the rules in
> `.github/copilot-instructions.md` (Google/GCP only, cache-first, $0, no secrets in git).

## Global definition of done
- [ ] Deployed on GCP: Cloud Run backend + Firebase Hosting frontend, publicly reachable.
- [ ] Auditing works end-to-end using Gemini, results cached in Firestore.
- [ ] The seed corpus produces a Rot Report that flags the planted contradiction.
- [ ] App renders a full report with **zero live model calls** (cache-first).
- [ ] No secrets committed. Works logged-out. Total spend ~$0.

---

## Phase 0 — Project setup
- [ ] Create/confirm GCP project; attach billing with the $300 free credit.
- [ ] Enable APIs:
      `gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com`
- [ ] Create Firestore in **Native mode** (region `us-central1`).
- [ ] Set a billing **budget alert at $5**.
- [ ] Create `.env.example` with: `GCP_PROJECT`, `GCP_LOCATION=us-central1`,
      `GEMINI_API_KEY` (AI Studio free-tier key for fallback).
- [ ] Add `.gitignore` excluding `.env`, `*.key`, `__pycache__/`, `node_modules/`.
- **Acceptance:** `gcloud firestore databases list` shows a database; `.env` is gitignored.

## Phase 1 — Repo scaffold
- [ ] Create structure:
      `backend/{main.py,audit.py,models.py,store.py,requirements.txt,Dockerfile,seed/}`
      `frontend/{index.html,app.js}`, `firebase.json`, `README.md`.
- [ ] `backend/requirements.txt`:
      `fastapi`, `uvicorn`, `google-genai`, `google-cloud-firestore`, `pydantic`.
- **Acceptance:** `pip install -r backend/requirements.txt` succeeds in a venv.

## Phase 2 — Seed corpus (the demo data)
- [ ] Add `backend/seed/corpus.json` — 15 docs with planted findings:
      1 contradiction pair (deploy.sh/Heroku vs GitHub Actions/Cloud Run),
      1 password-policy contradiction (90-day rotation vs no-rotation),
      1 deprecated (Stackdriver/Nagios), 2 stale (2021 VPN, 2021 DB backup),
      rest healthy.
- [ ] Add `backend/seed/EXPECTED_FINDINGS.md` (ground truth, NOT fed to the model).
- **Acceptance:** `corpus.json` parses and has 15 entries with
      `id,title,source,last_updated,body`.

## Phase 3 — Model layer (`models.py`)
- [ ] Implement Google-only clients: Vertex (Flash/Pro) + AI Studio key (free) + Gemma.
- [ ] `call_model()` returns JSON text; raise `QuotaError` on 429, `ModelError` otherwise.
- [ ] Model names read from env, pinned (e.g. `gemini-2.5-flash`, `gemini-2.5-pro`, `gemma-3-27b-it`).
- **Acceptance:** a throwaway script calls Flash on Vertex and gets valid JSON back.

## Phase 4 — Audit engine (`audit.py` + `store.py`)
- [ ] `store.py`: `get_audit(doc_id)` / `save_audit(doc_id, payload)` on Firestore.
- [ ] `audit.py`: Pydantic `AuditResult`, `build_prompt`, cache-first `audit_document`,
      `audit_corpus`, and the routing ladder:
      Flash → escalate to Pro if `confidence<0.55` or `uncertain` → free/Gemma on quota
      → heuristic floor.
- [ ] Heuristic fallback flags deprecated terms + docs older than 2 years.
- **Acceptance:** `python backend/smoke_test.py` flags `deployment-guide` as
      **contradictory** vs `cicd-pipeline`, and the result is cached in Firestore.

## Phase 5 — API (`main.py`, Cloud Run)
- [ ] FastAPI endpoints:
      `POST /audit` → loads corpus, runs `audit_corpus`, caches, returns summary.
      `GET /report` → returns all cached audits (sorted: lowest confidence first).
      `GET /healthz` → `{"ok": true}`.
- [ ] Load `seed/corpus.json` on startup; serve corpus docs for the UI.
- [ ] Enable permissive CORS for the Firebase Hosting origin.
- [ ] `Dockerfile` (python:3.11-slim, uvicorn on `$PORT`).
- **Acceptance:** `uvicorn main:app` locally → `POST /audit` then `GET /report`
      returns the ranked report JSON.

## Phase 6 — Deploy backend to Cloud Run
- [ ] `gcloud run deploy truthkeeper-api --source backend --region us-central1 \
        --allow-unauthenticated --min-instances=0 --max-instances=2 \
        --set-env-vars GCP_PROJECT=...,GCP_LOCATION=us-central1`
- [ ] Store `GEMINI_API_KEY` via Secret Manager / `--set-secrets`, NOT in code.
- [ ] Grant the Cloud Run service account Vertex AI User + Firestore roles.
- **Acceptance:** `curl https://<cloud-run-url>/report` returns JSON from the cloud.

## Phase 7 — Frontend (Firebase Hosting)
- [ ] `frontend/index.html` + `app.js`: a clean Rot Report dashboard that calls
      the Cloud Run `GET /report`.
- [ ] For each doc: title, confidence score (color-coded), status badge,
      contradictions with cited evidence, suggested fix. Sort worst-first.
- [ ] A "Run Audit" button hitting `POST /audit` (nice-to-have; report must render
      from cache without it).
- [ ] `firebase init hosting` + `firebase deploy --only hosting`.
- **Acceptance:** public Firebase URL shows the Rot Report; open it in **incognito**
      (logged-out) and it still works.

## Phase 8 — Evaluation-proofing
- [ ] Pre-run `POST /audit` so Firestore is fully populated before the demo.
- [ ] Add graceful "showing cached audit" state; never show a crash/empty screen.
- [ ] Confirm the routing ladder degrades cleanly (simulate quota by unsetting the key).
- [ ] Verify cold-start loads acceptably; add a frontend loading state.
- [ ] README: architecture, how Firebase/Firestore/Cloud Run/Gemini are used,
      local run + deploy steps, and the live URLs.
- **Acceptance:** fresh incognito visit renders the full report in < 3s with no errors.

## Phase 9 — Submission assets
- [ ] Record a **≤4:00** demo video against the **live** URL:
      problem → upload/seed → run audit → Rot Report → the "aha"
      (`deployment-guide` flagged only because it contradicts `cicd-pipeline`).
- [ ] Write the brief description naming Firebase, Firestore, Cloud Run, Gemini.
- [ ] Push public GitHub repo (verify NO secrets in history).
- [ ] Fill the pitch deck (prescribed template).
- **Acceptance:** all 4 mandatory deliverables ready; live URL confirmed working.

---

## Guardrails (apply throughout)
- Google models only (Gemini + Gemma). Never add non-Google providers.
- Cache every audit in Firestore; never re-audit on page load.
- Cloud Run `min-instances=0`. No AlloyDB, no standing Vertex AI Search index, no BigQuery.
- Secrets only via env/Secret Manager. Budget alert at $5. Delete resources after eval.

## Done when
The live Firebase URL shows a ranked Rot Report (worst-first) with cited evidence,
backed by Cloud Run + Firestore + Gemini, reproducible from a clean `git clone` by
following the README — at ~$0 cost.
