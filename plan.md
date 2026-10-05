# TruthKeeper — Copilot Project Instructions

You are helping build **TruthKeeper**, an AI Knowledge Auditor for the
AI Builder Cup 2026 hackathon (track: Future of Work & Enterprise Productivity).
Always follow these instructions in this repo.

## What we're building
Unlike enterprise search/copilots that ANSWER FROM documents, TruthKeeper
INTERROGATES them: it detects contradictions, stale content, and deprecated
references across a knowledge base, then produces a ranked, evidence-backed
"Rot Report" with confidence scores and suggested fixes.

One-liner: "Everyone built AI to answer from your documents.
We built the AI that doesn't trust them — and proves which ones are wrong."

## Hard constraints (never violate)
- **Google / GCP only.** Models must be Google-family (Gemini, Gemma).
  NEVER use or suggest non-Google models (no Grok, GPT, Llama, Claude) in the
  product path.
- **Mandatory tech, must be visibly used:** Firebase, Firestore, Cloud Run, Gemini.
- **Stay free:** use GCP always-free tiers + the $300 credit. Target $0 spend.
- **Evaluation-proof:** the deployed prototype must work live, logged-out, with
  no external dependencies (no Slack, no VPN, no private endpoints).
- Keep secrets in Secret Manager / env vars. NEVER commit keys. Keep `.env` in
  `.gitignore`.

## Tech stack
- Reasoning: Gemini Flash (core) + Gemini Pro (escalation for hard docs)
- Free fallback: Gemini free tier + Gemma (open, Google-family)
- Backend: Cloud Run (Python/FastAPI, min-instances=0, max=2)
- Data: Firestore (audit records, contradiction graph, cache)
- Frontend: Firebase Hosting + Firebase Auth
- Secrets: Secret Manager
- Optional: Document AI (PDF parsing) only if time allows

## Architecture — CACHE-FIRST (critical)
Audit each document ONCE, store the result in Firestore. The deployed app READS
cached results, so judges trigger ZERO live model calls. This makes it both free
(no per-view cost) and flawless (no live-API dependency at evaluation time).

Flow: User -> Firebase Hosting/Auth -> Cloud Run (audit API) -> Firestore cache
      Cloud Run -> model router -> Gemini Flash / Pro / Gemma

## Model routing (resilience ladder — try top first)
- Layer 0: Firestore cache          (free, default render path)
- Layer 1: Gemini Flash             (95% of auditing, cheap)
- Layer 2: Gemini Pro               (escalate only low-confidence/ambiguous docs)
- Layer 3: Gemini free tier / Gemma (free fallback if quota hit)
- Layer 4: rule-based heuristics    (never-fails floor; never a broken screen)

## Data model (Firestore)
- `documents/{id}`: title, body, source, last_updated
- `audits/{id}`: doc_id, confidence (0-1), status, model_used, evidence[],
  suggested_fix, created_at
- `contradictions/{id}`: doc_a, doc_b, explanation, evidence

## Audit output contract (Gemini must return this JSON)
{
  "confidence": 0.0-1.0,
  "status": "healthy" | "stale" | "contradictory" | "deprecated" | "uncertain",
  "contradictions": [{ "other_doc": "...", "explanation": "...", "evidence": "..." }],
  "evidence": ["quoted clause/line that triggered the flag"],
  "suggested_fix": "..."
}
Rule: if evidence is insufficient, return status "uncertain" — DO NOT guess.

## Repo structure
backend/
  main.py          # FastAPI: POST /audit (run+cache), GET /report (read cache)
  audit.py         # audit_document() + routing ladder + Firestore caching
  models.py        # Gemini Flash/Pro/Gemma clients, structured JSON output
  store.py         # Firestore read/write
  seed/            # 10-20 sample docs with PLANTED findings
  requirements.txt
  Dockerfile
frontend/          # Firebase Hosting (simple UI: upload + Rot Report)
firebase.json
.gitignore
README.md

## Seed corpus (defines the demo "aha")
15 sample docs where: 2 CONTRADICT each other, 1 references a DEPRECATED tool,
1 is obviously STALE. The aha moment: a doc that LOOKS fine is flagged because
it contradicts another — something keyword search would never catch.

## Build order (follow strictly)
1. GCP setup: project, $300 credit, enable run/aiplatform/firestore/
   cloudbuild/secretmanager APIs, Firestore (Native), budget alert $5.
2. Write seed corpus (backend/seed/).
3. Build audit_document() + models.py; prove it finds the planted contradiction
   LOCALLY before anything else.
4. Wrap in Cloud Run (main.py, Dockerfile); deploy; verify GET /report via curl.
5. Firebase frontend: upload view + Rot Report view; deploy; test logged-out.
6. Add fallback ladder + graceful "showing cached audit" degrade state.
7. Pre-run the audit so Firestore is populated for an instant demo.
8. Record <=4 min video against the live URL; push repo (no keys).

## Cost rules (keep $0)
- Gemini Flash primary; Pro only on escalation (rare). Cache every audit.
- Cloud Run min-instances=0, max-instances=2.
- No AlloyDB, no standing Vertex AI Search index, no BigQuery streaming.
- Budget alert $5; delete resources after evaluation.

## Coding conventions
- Python 3.11+, FastAPI, type hints, pydantic models for the audit contract.
- Use the google-genai SDK for Gemini. Pin versions in requirements.txt.
- Keep functions small; one model-router entry point: audit_document(doc, corpus).
- No secrets in code. Read config from env vars.

## Deploy commands
gcloud run deploy truthkeeper-api --source backend --region us-central1 \
  --allow-unauthenticated --min-instances=0 --max-instances=2
firebase deploy --only hosting
