# TruthKeeper — Architecture

## One-liner
Everyone built AI to answer from your documents. We built the AI that doesn't
trust them — and proves which ones are wrong.

## Request flow
```
┌────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Browser   │────▶│  Firebase Hosting     │────▶│  Cloud Run (FastAPI)│
│ (logged-out)│    │  index.html + app.js  │     │  /report  /audit    │
└────────────┘     └──────────────────────┘     └──────────┬──────────┘
       ▲                                                     │
       │                      cache-first read               ▼
       │                                            ┌─────────────────┐
       └────────────── Rot Report (JSON) ───────────│   Firestore     │
                                                     │  audits cache   │
                                                     └────────┬────────┘
                                                              │ miss / POST /audit
                                                              ▼
                                                     ┌─────────────────┐
                                                     │  Model router   │
                                                     │ Flash→Pro→Gemma │
                                                     │ →heuristic floor│
                                                     └─────────────────┘
```

## Cache-first (the key design decision)
Each document is audited **once**; the result is written to the Firestore
`audits` collection. The deployed app's default render path is `GET /report`,
which is a **pure cache read** — a judge's visit triggers **zero live model
calls**. This makes the demo both **free** (no per-view cost) and **flawless**
(no live-API dependency at evaluation time).

## Resilience ladder
| Layer | Backend                     | When                                    |
|-------|-----------------------------|-----------------------------------------|
| 0     | Firestore cache             | default render path                     |
| 1     | Gemini Flash (Vertex)       | 95% of auditing                         |
| 2     | Gemini Pro (Vertex)         | escalate if confidence < 0.55 / uncertain |
| 3     | Gemini free tier / Gemma    | on quota (429)                          |
| 4     | Rule-based heuristics       | never-fails floor (deprecated terms, age) |

## Mandatory tech usage
- **Gemini** — reasoning engine (`backend/models.py`, `audit.py`).
- **Firestore** — corpus + cached audits (`backend/store.py`); the cache-first core.
- **Cloud Run** — hosts the FastAPI audit service, `min-instances=0`, `max-instances=2`.
- **Firebase Hosting** — serves the Rot Report dashboard (`frontend/`).

## Data model (Firestore)
- `audits/{doc_id}`: `confidence`, `status`, `contradictions[]`, `evidence[]`,
  `suggested_fix`, `model_used`, `created_at`, `title`.

## Cost controls
`min-instances=0`, Flash-primary with rare Pro escalation, every audit cached,
no AlloyDB / standing Vertex AI Search index / BigQuery streaming, $5 budget alert.
