# TruthKeeper — Winner-Level MVP Plan

> **Positioning:** TruthKeeper is the **trust layer for enterprise AI**. Before any
> AI answers from your knowledge, TruthKeeper verifies it's still true — and exposes
> a **Trust API** so every copilot in the org can check a document before using it.
>
> One-liner: *"Everyone built AI to answer from your documents. We built the AI that
> doesn't trust them — and proves which ones are wrong."*

This plan extends the working MVP (audit engine + Rot Report) into a platform story.
It reuses what exists: [backend/audit.py](backend/audit.py), [models.py](backend/models.py),
[store.py](backend/store.py), [main.py](backend/main.py), and the animated
[frontend/](frontend/). Everything stays Google-only, cache-first, and $0.

---

## 1. Enterprise problem → feature mapping (why each feature earns its place)

| Enterprise pain | Consequence | Feature that solves it |
|---|---|---|
| Docs silently go stale / contradict each other | Outages from bad runbooks, wrong decisions | **Contradiction + rot detection** (built) |
| No one knows which docs to fix first | Wasted effort, risk lingers | **Ranked Rot Report** (built) + **Org Health Score** |
| Can't see how knowledge conflicts relate | Hidden conflict clusters | **Knowledge-health graph** |
| AI copilots cite rotten docs confidently | Confident wrong answers at scale | **Trust API + guardrailed copilot** |
| Fixes applied blindly by AI | Loss of control, compliance risk | **Human-in-the-loop approval** |
| "Does it work on *our* docs?" | Judges/buyers stay skeptical | **Paste-your-own-docs** (one live path) |

---

## 2. Feature set (what we build)

### F1 — Knowledge-Health Graph (flagship visual)
Node-link view: each doc is a node (color = status, size = risk), each contradiction is
a glowing edge. Clicking a node opens its audit card. Makes the "living knowledge-health
graph" claim literal.
- **Backend:** `GET /graph` → `{ nodes:[{id,title,status,confidence}], edges:[{a,b,explanation,evidence}] }`, derived from cached audits + the new `contradictions` collection.
- **Frontend:** lightweight force/radial layout on canvas (no external lib); edges pulse on hover; click → scrolls to card.
- **GCP/cost:** pure Firestore read. $0.

### F2 — Trust API + Guardrailed Copilot (the money moment)
The platform wedge: other AIs call TruthKeeper before trusting a doc.
- **Backend:**
  - `GET /verify?doc_id=...` → `{ trusted: bool, score, status, reason, evidence[] }` (thin read over cached audit; `trusted = status in {healthy} and score >= 0.7`).
  - `POST /ask` → `{ question }` → retrieves the best-matching corpus doc (keyword match, cache-first), returns `{ answer, source: doc_id, trust: <verify result>, warning? }`. If the source doc is low-trust, `warning` explains why and the UI shows a red interstitial.
- **Frontend:** an "Ask your knowledge base" box. Answer renders with a **trust banner** (green/amber/red). For a flagged source, the copilot **refuses/warns**: "⚠️ This answer is based on `deployment-guide`, flagged *contradictory* vs `cicd-pipeline`."
- **GCP/cost:** `/verify` is a read ($0). `/ask` is cache-first; demo questions are pre-seeded so judging triggers no live call.

### F3 — Org Knowledge-Health Score (exec KPI)
A single "Knowledge Health: NN/100" gauge with a breakdown (how many contradictory/stale/
deprecated) and a trend line (seeded history).
- **Backend:** `GET /health-score` → `{ score, grade, breakdown, history[] }`. Score = weighted function of audit statuses/confidence.
- **Frontend:** animated gauge in the hero/dashboard.
- **GCP/cost:** computed from cached audits. $0.

### F4 — Human-in-the-Loop Approval (governance)
Each suggested fix gets **Accept** / **Dismiss**. Decisions persist and change the doc's
state (e.g. "fix accepted — pending publish").
- **Backend:** `POST /decisions` → `{ doc_id, action: "accept"|"dismiss", note? }` writes `decisions/{doc_id}`; `GET /report` joins decisions into each audit.
- **Frontend:** buttons on each card; optimistic UI + toast.
- **GCP/cost:** Firestore write. $0.

### F5 — Paste-Your-Own-Docs (interactive proof, optional live path)
A judge pastes 2+ docs; TruthKeeper audits them live and catches the conflict.
- **Backend:** `POST /audit/adhoc` → `{ docs:[...] }` audits provided docs against each other (and optionally the corpus) **without caching**; returns results. This is the **only** live-model path.
- **Frontend:** modal with two text areas pre-filled with a conflicting example; "Audit these" button; graceful fallback to a canned result if the model is unavailable.
- **GCP/cost:** one live Gemini call on demand, Flash-only, no cache write. Guardrailed; off the default path.

---

## 3. API surface (additions to [API_CONTRACT.md](API_CONTRACT.md))

| Method | Path | Purpose | Model call? |
|---|---|---|---|
| GET | `/report` | ranked cached audits (exists) | no |
| POST | `/audit` | audit corpus, cache (exists) | yes (first run) |
| GET | `/docs-list` | raw corpus (exists) | no |
| GET | `/graph` | nodes + contradiction edges | no |
| GET | `/verify` | trust verdict for a doc (Trust API) | no |
| POST | `/ask` | guardrailed answer + trust banner | no (pre-seeded) |
| GET | `/health-score` | org KPI + breakdown + history | no |
| POST | `/decisions` | human accept/dismiss a fix | no |
| POST | `/audit/adhoc` | audit pasted docs (optional live) | yes (on demand) |

All read endpoints are cache-first ⇒ judging triggers **zero** live calls.

---

## 4. Data model additions (Firestore)
- `audits/{doc_id}` — existing audit records.
- `contradictions/{pair_id}` — `{ doc_a, doc_b, explanation, evidence, detected_at }`, written during `audit_corpus` from each result's `contradictions[]`. Powers `/graph`.
- `decisions/{doc_id}` — `{ action, note, decided_at }`. Powers the approval loop.
- `health_history/{date}` — `{ score, breakdown }` snapshot (seed a few points for the trend).

---

## 5. Build phases (ordered, each with an acceptance check)

**Phase A — Backend trust endpoints**
Add `/verify`, `/graph`, `/health-score`, `/decisions`; write `contradictions` during
`audit_corpus`; join `decisions` into `/report`.
*Accept:* `curl /verify?doc_id=deployment-guide` returns `trusted:false` with reason;
`/graph` returns the deployment-guide↔cicd-pipeline edge; `/health-score` returns a number.

**Phase B — Knowledge-health graph (frontend)**
Canvas node-link view; status colors; glowing contradiction edges; click→card.
*Accept:* graph renders the conflict cluster; clicking a node focuses its report card.

**Phase C — Trust banner + guardrailed copilot (frontend + `/ask`)**
"Ask your knowledge base" box; answer with green/amber/red trust banner; refusal/warning
for low-trust sources.
*Accept:* asking "how do I deploy?" returns the deploy answer **with a red warning** citing
the contradiction.

**Phase D — Org Health Score + approval loop (frontend)**
Animated gauge; Accept/Dismiss on cards wired to `/decisions`.
*Accept:* score animates on load; accepting a fix persists and updates the card state.

**Phase E — Paste-your-own (optional live) + polish**
Modal + `/audit/adhoc` with graceful fallback; demo-script + README/pitch updated to the
trust-layer framing.
*Accept:* pasting the sample conflicting docs returns a contradictory verdict live; falls
back cleanly when offline.

**Phase F — Deploy + pre-populate (ties into existing task.md Phases 0/6/7)**
Cloud Run + Firebase deploy; pre-run `/audit`; seed `health_history`.
*Accept:* incognito live URL renders graph + report + score from cache in <3s, zero model calls.

---

## 6. Demo arc (≤4 min) — Villain → Hero → Wow → Payoff → Platform
1. **Villain:** a copilot confidently gives wrong deploy steps from a stale doc.
2. **Hero:** the Rot Report catches the contradiction, worst-first, with cited evidence.
3. **Wow:** the Knowledge-Health Graph lights up the conflict cluster; Health Score = low.
4. **Payoff:** re-ask the copilot → TruthKeeper **intercepts and warns** (`/ask` + trust banner).
5. **Platform:** "any AI in your org can call this" → the **Trust API** (`/verify`). Live, $0, on GCP.

---

## 7. Guardrails (unchanged, enforced)
- Google models only (Gemini/Gemma). Cache every audit. Cloud Run `min-instances=0`.
- Only `/audit` and `/audit/adhoc` ever call a model; everything judges touch is a cache read.
- No AlloyDB / standing Vertex AI Search index / BigQuery. $5 budget alert. Secrets via env/Secret Manager.
