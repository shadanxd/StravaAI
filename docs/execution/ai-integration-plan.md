## AI Integration Plan (Pre-MVP)

### Introduction

The goal is to layer AI-generated insights on top of the existing authentication, user, activity, and analytics modules to deliver immediate value with minimal engineering overhead. We will use existing data sources and endpoints (`/api/activities`, `/api/analytics`) to construct rich prompts and generate concise, actionable insights for:

- Per-activity takeaways and coaching tips
- Weekly/Monthly user summaries and sport-wise analysis
- Lightweight training suggestions grounded in recent trends

Constraints and security:
- Store provider API keys via environment variables (e.g., `OPENAI_API_KEY`). Do not auto-generate secrets; load from `.env`.
- Access/refresh tokens remain encrypted at rest and never leave the server. Keys are provided via `.env` and must not be generated in code. [Security note aligns with existing encryption utilities and env-based key management.]

### Strategy

Implementation options considered:

- On-demand generation only
  - Pros: Minimal infra; pay-per-use; fast to ship.
  - Cons: Latency on first request; repeated cost if no caching.

- Background generation on sync + cache
  - Pros: Zero-latency reads after sync; amortizes cost.
  - Cons: Slightly more moving parts; needs idempotency + TTL.

- Hybrid (Recommended for MVP)
  - Generate insights for the N most recent activities during `/api/activities/sync`.
  - On-demand generation for any activity missing insights; write-back to DB for caching.
  - Periodic (weekly/monthly) summaries generated on-demand, with a short TTL cache (e.g., 24h) keyed by `(user_id, period, end_date)`.

Data and context sources:
- User profile: `users` collection (name, sex, weight, city/country), milestones
- Activities: `activities` collection (distance, moving_time, elevation, HR, speed, type, timestamps)
- Analytics: `get_analytics_summary`, `get_trend_timeseries`, and sport-specific stats helpers

Prompting approach:
- System prompt: role, safety, style (brief, specific, non-clinical), metric units (SI), and data reliability notes.
- Context builder: merges per-activity raw fields + derived metrics + short trend snippets.
- Output schema: compact JSON with stable keys to store under `activity.insights` and for summaries under a new insights cache collection.

Example system prompt skeleton (for reference):

```text
You are an endurance training assistant. Be concise and actionable. Use SI units.
Given the athlete profile, this activity, and recent trends, output:
1) one-sentence summary; 2) 2–3 coaching tips; 3) tags [recovery, tempo, threshold, endurance, intervals, hills].
Maintain safety: do not give medical advice; highlight anomalies and advise rest when appropriate.
```

Example output schema (stored in `activity.insights`):

```json
{
  "summary": "Solid aerobic ride with steady cadence and modest elevation.",
  "coach_tips": ["Hydrate more in similar temps.", "Extend endurance block by 10–15 min next session."],
  "tags": ["endurance"],
  "model": "provider:model-name",
  "generated_at": "2025-01-01T12:00:00Z",
  "context_hash": "..."
}
```

API design (proposed):
- `POST /api/insights/activity/{id}/generate` – generate and persist insights for a single activity if missing or `force=true`.
- `GET /api/insights/activity/{id}` – fetch persisted insights.
- `POST /api/insights/bulk/recent?limit=10` – generate for most recent N activities without insights.
- `GET /api/insights/summary?period=week|month` – generate or fetch cached user summary across sports using analytics pipelines.

Storage design:
- Extend `activities` documents with `insights` field (dict) containing the schema above.
- Optional: create `insight_summaries` collection keyed by `(user_id, period, window_end)` for weekly/monthly summaries.

Operational considerations:
- Idempotency: compute and compare a `context_hash` to avoid duplicate generation.
- Caching: write-back on generation; TTL for summaries (e.g., 24h) to control cost.
- Rate limiting: bound concurrent generations per user/session.
- Privacy: redact PII; do not send tokens or raw GPS coordinates unless needed.

### Executive Checklist (MVP)

- Folder structure
  - **Create** `app/ai/` with:
    - `providers.py` – thin LLM client wrapper (env-driven provider/model; `OPENAI_API_KEY` via `.env`).
    - `prompt_builder.py` – system prompts and context builders (activity, weekly, monthly).
    - `insight_service.py` – orchestration: build context → call provider → validate → persist.

- Environment & security
  - **Env vars**: `OPENAI_API_KEY`, `AI_PROVIDER`, `AI_MODEL`.
  - **Do not** generate encryption keys in code; load from `.env` and keep Strava tokens encrypted at rest.

- Database
  - **Add** `insights` field to `activities` documents when writing results.
  - **Optional**: new `insight_summaries` collection with TTL index of ~24h.

- Endpoints
  - **New router** `app/ai_routes.py`:
    - `POST /api/insights/activity/{id}/generate[?force=true]`
    - `GET /api/insights/activity/{id}`
    - `POST /api/insights/bulk/recent?limit=10`
    - `GET /api/insights/summary?period=week|month`
  - **Wire** router in `main.py` alongside existing routes.

- Sync integration
  - **Hook** into `/api/activities/sync` to generate insights for the N most recent activities lacking insights (e.g., N=5) after DB upsert.

- Validation & safety
  - **JSON schema** validation for model outputs; fallback to minimal text if parsing fails.
  - **Guardrails**: truncate overly long outputs; remove PII; ensure non-medical tone.

- Telemetry & cost control
  - **Log** model, tokens, latency; sample only non-sensitive metadata.
  - **Cache**: short TTL summaries; write-back per-activity to avoid re-generation.

- Testing
  - **Unit**: prompt builder determinism given fixed fixtures.
  - **Integration**: generate insights for fixture activities; assert persistence and schema.

- Rollout
  - **Feature flag** `AI_INSIGHTS_ENABLED` to allow staged rollout.

### Notes on Provider Setup

- Default to a well-supported hosted LLM via environment-configured provider/model.
- Keys must be supplied via `.env` and never generated automatically. Ensure encryption key usage remains unchanged and consistent with `app/utils/encryption.py`.


