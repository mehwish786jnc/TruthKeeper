# TruthKeeper — API Contract & Connections

> Reference for how TruthKeeper is wired: every API endpoint, every service
> connection, the data model, and the end-to-end request flow.

TruthKeeper **interrogates** a knowledge base — it detects contradictions, stale
content, and deprecated references and produces a ranked, evidence-backed **Rot
Report**. The design is **cache-first**: documents are audited once, results are
stored in Firestore, and the live app serves cached results so a visitor triggers
**zero live model calls**.

---

## 1. System overview

```
┌──────────────┐   HTTPS/JSON    ┌──────────────────────┐   SDK (ADC)   ┌─────────────┐
│   Browser    │ ───────────────▶│   Cloud Run           │ ─────────────▶│  Firestore   │
│ (Firebase    │   GET /report   │   FastAPI service     │   audits/*    │  (audits)    │
│  Hosting)    │◀─────────────── │   main.py             │◀───────────── │              │
└──────────────┘                 │                       │               └─────────────┘
       │   POST /audit            │   audit.py (ladder)   │   SDK (ADC / API key)
       └─────────────────────────▶│   models.py          │ ──────────────▶ Gemini
                                  └──────────────────────┘   Flash / Pro / Gemma
```

Three connection tiers:
1. **Browser → Cloud Run** — HTTP/JSON (this document's main API).
2. **Cloud Run → Firestore** — cached audit storage (the cache-first core).
3. **Cloud Run → Gemini** — reasoning, only during `POST /audit`.

---

## 2. HTTP API (Browser → Cloud Run)

Base URL: `window.CONFIG.CLOUD_RUN_URL` (see [frontend/config.js](frontend/config.js)).
- Local: `http://localhost:8080`
- Deployed: `https://truthkeeper-api-<hash>-uc.a.run.app`

CORS: `Access-Control-Allow-Origin: *` (static Firebase Hosting origin).
All responses are `application/json`.

### 2.1 `GET /report` — the default render path
Returns every cached audit, sorted worst-first (lowest confidence). **Pure
Firestore read — never calls a model.**

**Request:** no params, no auth.

**Response `200`:**
```json
{
  "count": 15,
  "audits": [
    {
      "doc_id": "deployment-guide",
      "title": "How to Deploy the Northwind API",
      "confidence": 0.18,
      "status": "contradictory",
      "contradictions": [
        {
          "other_doc": "cicd-pipeline",
          "explanation": "Says deploy via deploy.sh to Heroku; cicd-pipeline says deploy.sh was removed and deploys go to Cloud Run.",
          "evidence": "run ./deploy.sh ... pushes it directly to our Heroku dynos"
        }
      ],
      "evidence": ["run ./deploy.sh from the repo root"],
      "suggested_fix": "Update to reference the GitHub Actions → Cloud Run pipeline; remove deploy.sh/Heroku instructions.",
      "model_used": "gemini-flash",
      "created_at": "2026-10-05T12:00:00+00:00"
    }
  ]
}
```

### 2.2 `POST /audit` — run / refresh the audit
Loads the seed corpus, runs the routing ladder for each **uncached** document
(cache-first), stores results in Firestore, and returns a summary.

**Request:**
- Query: `force` (bool, default `false`) — `true` re-audits every doc, bypassing cache.
- Header: `X-Audit-Token: <token>` — **required only when the server has `AUDIT_TOKEN` set** (deployed). Omitted in local dev.

**Response `200`:**
```json
{
  "audited": 15,
  "flagged": 5,
  "statuses": {
    "deployment-guide": "contradictory",
    "cicd-pipeline": "contradictory",
    "password-policy": "contradictory",
    "security-standards-2025": "contradictory",
    "monitoring-setup": "deprecated",
    "vpn-access": "stale",
    "database-backup": "stale",
    "onboarding-checklist": "healthy"
  }
}
```

**Errors:**
- `401 Unauthorized` — `AUDIT_TOKEN` is set on the server and the header is missing/wrong.

> **Cost note:** `/audit` is the only endpoint that calls a model. It is
> cache-first, so repeated calls (without `force`) re-audit nothing and cost ~$0.
> The token is drive-by abuse deterrence; the real protection is cache-first +
> pre-populated Firestore so the live demo path (`/report`) is model-free.

### 2.3 `GET /docs-list` — raw corpus (backend-only)
Returns the 15 source documents. Available for tooling / a future Knowledge Base
view; **not surfaced in the MVP UI**.

**Response `200`:** `CorpusDoc[]` (see §4).

### 2.4 `GET /healthz` — liveness
**Response `200`:** `{ "ok": true }`

---

## 3. Service connections

### 3.1 Cloud Run → Firestore
- SDK: `google-cloud-firestore`; auth via **Application Default Credentials**
  (local = `gcloud auth application-default login`; deployed = Cloud Run service account).
- Project from `GCP_PROJECT`. Collection `audits`, doc id = `doc_id`.

| Function ([store.py](backend/store.py)) | Operation | Caller |
|---|---|---|
| `get_audit(doc_id)` | get `audits/{doc_id}` | cache check (ladder Layer 0) |
| `save_audit(doc_id, payload)` | set `audits/{doc_id}` | after a doc is audited |
| `get_all_audits()` | stream `audits` | `GET /report` |

### 3.2 Cloud Run → Gemini (routing ladder)
Reached only from `POST /audit` via `_run_ladder` in [audit.py](backend/audit.py).
Each layer is tried top-first; failures fall through.

| Layer | Transport | Model (env) | Auth | When |
|---|---|---|---|---|
| 0 Cache | Firestore | — | ADC | always first |
| 1 Flash | Vertex AI | `MODEL_FLASH`=`gemini-2.5-flash` | ADC / service account | primary (every doc) |
| 2 Pro | Vertex AI | `MODEL_PRO`=`gemini-2.5-pro` | ADC / service account | escalate if `confidence < 0.55` or `status == "uncertain"` |
| 3 Gemma/free | AI Studio API | `MODEL_GEMMA`=`gemma-3-27b-it` | `GEMINI_API_KEY` | on quota (`QuotaError`) from Vertex |
| 4 Heuristic | in-process | — | — | all live layers failed (never-fails floor) |

Model calls use `temperature=0.1`, `response_mime_type="application/json"`.
Errors are normalized ([models.py](backend/models.py)): `QuotaError` (429/quota) →
step down the ladder; `ModelError` (everything else) → fall through.

---

## 4. Data model

**CorpusDoc** (seed input — [backend/seed/corpus.json](backend/seed/corpus.json)):
```json
{ "id": "deployment-guide", "title": "...", "source": "wiki/...", "last_updated": "2022-03-14", "body": "..." }
```

**AuditResult** (model output contract + cached record — [audit.py](backend/audit.py)):
```json
{
  "doc_id": "string",
  "title": "string",
  "confidence": 0.0,
  "status": "healthy | stale | contradictory | deprecated | uncertain",
  "contradictions": [{ "other_doc": "string", "explanation": "string", "evidence": "string" }],
  "evidence": ["string"],
  "suggested_fix": "string",
  "model_used": "gemini-flash | gemini-pro | gemma | heuristic",
  "created_at": "ISO-8601 string"
}
```
Rule: if evidence is insufficient, the model must return `status: "uncertain"` — never guess.

Firestore stores `AuditResult` documents in `audits/{doc_id}`.

---

## 5. Configuration

| Variable | Where | Local | Deployed |
|---|---|---|---|
| `CLOUD_RUN_URL` | frontend/config.js | `http://localhost:8080` | Cloud Run URL |
| `AUDIT_TOKEN` | frontend/config.js + backend env | unset (auth off) | Secret Manager |
| `GCP_PROJECT` | backend env | `.env` | `--set-env-vars` |
| `GCP_LOCATION` | backend env | `us-central1` | `--set-env-vars` |
| `GEMINI_API_KEY` | backend env | `.env` | Secret Manager `--set-secrets` |
| `MODEL_FLASH` / `MODEL_PRO` / `MODEL_GEMMA` | backend env | optional overrides | optional overrides |

**Required Cloud Run service-account IAM roles:**
`roles/aiplatform.user` (Vertex/Gemini), `roles/datastore.user` (Firestore),
`roles/secretmanager.secretAccessor` (secrets).

---

## 6. End-to-end request flow

**Judge opens the live app (model-free path):**
1. Browser loads static assets from Firebase Hosting.
2. `app.js` calls `GET {CLOUD_RUN_URL}/report`.
3. Cloud Run reads `audits` from Firestore and returns them worst-first.
4. UI renders cards (status badge, confidence, contradictions + evidence, fix). No model call.

**Operator pre-populates before the demo (one-time):**
1. `POST /audit` (with `X-Audit-Token` when deployed).
2. For each uncached doc: Firestore miss → Flash → (maybe Pro) → (Gemma on quota) → (heuristic floor).
3. Each result is written to `audits/{doc_id}`.
4. Subsequent `/report` calls serve purely from cache.

---

## 7. Quick reference (curl)

```bash
# Health
curl https://<run-url>/healthz

# Pre-populate (deployed: include the token)
curl -X POST https://<run-url>/audit -H "X-Audit-Token: $AUDIT_TOKEN"

# Force a full re-audit
curl -X POST "https://<run-url>/audit?force=true" -H "X-Audit-Token: $AUDIT_TOKEN"

# Read the Rot Report (no auth, no model calls)
curl https://<run-url>/report
```
