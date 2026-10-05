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

## Architecture — CACHE-FIRST (critical)
Audit each document ONCE, store the result in Firestore. The deployed app READS
cached results, so judges trigger ZERO live model calls. Free + flawless.

## Model routing (resilience ladder — try top first)
- Layer 0: Firestore cache          (free, default render path)
- Layer 1: Gemini Flash             (95% of auditing, cheap)
- Layer 2: Gemini Pro               (escalate only low-confidence/ambiguous docs)
- Layer 3: Gemini free tier / Gemma (free fallback if quota hit)
- Layer 4: rule-based heuristics    (never-fails floor; never a broken screen)

## Audit output contract (Gemini must return this JSON)
{
  "confidence": 0.0-1.0,
  "status": "healthy" | "stale" | "contradictory" | "deprecated" | "uncertain",
  "contradictions": [{ "other_doc": "...", "explanation": "...", "evidence": "..." }],
  "evidence": ["quoted clause/line that triggered the flag"],
  "suggested_fix": "..."
}
Rule: if evidence is insufficient, return status "uncertain" — DO NOT guess.

## Coding conventions
- Python 3.11+, FastAPI, type hints, pydantic models for the audit contract.
- Use the google-genai SDK for Gemini. Pin versions in requirements.txt.
- Keep functions small; one model-router entry point: audit_document(doc, corpus).
- No secrets in code. Read config from env vars.
