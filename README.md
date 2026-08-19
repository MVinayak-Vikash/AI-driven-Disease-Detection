# AI Early-Risk & Referral Navigator

FastAPI backend for a multi-device, Supabase-backed early-risk screening prototype. It is clinical decision support only: it reports elevated risk indicators and recommended follow-up, never a definitive diagnosis.

## Architecture

Next.js authenticates users with Supabase Auth and sends its access token to FastAPI. FastAPI verifies the token through Supabase Auth, forwards the same token to Supabase PostgREST, and relies on Row Level Security (RLS) for data isolation. ESP32 devices authenticate to FastAPI with a one-time pairing credential; their credentials are SHA-256 hashed in Supabase and service-role access remains server-side only.

`ESP32 + MAX30102 → FastAPI REST → Supabase readings → signal features → AI provider → Supabase assessment → frontend`

## Setup

1. Create a Supabase project and apply [the migration](supabase/migrations/202608170001_initial_schema.sql) with the Supabase CLI or SQL editor.
2. Copy `.env.example` to `.env` and provide the Supabase URL, anon key, and (server-only) service role key.
3. Install dependencies: `python -m pip install -r requirements.txt`
4. Start the API: `uvicorn app.main:app --reload`
5. Open `http://localhost:8000/docs` for the API schema and `GET /health` for a health check.

Never put `SUPABASE_SERVICE_ROLE_KEY` in the frontend or ESP32 firmware.

## Authentication and APIs

Protected browser endpoints require `Authorization: Bearer <supabase_access_token>`. The backend obtains the canonical user UUID from `GET /auth/v1/user`; supplied user IDs are never trusted.

- Profiles: `GET/PUT /api/profile`, `GET /api/me`
- Devices: `POST/GET /api/devices`, `GET/DELETE /api/devices/{device_id}`
- Sessions: `POST/GET /api/sessions`, `GET /api/sessions/{id}`, `POST /api/sessions/{id}/finish`
- Sensors: `POST /api/sessions/{id}/readings`, `GET /api/sessions/{id}/readings`, `POST /api/devices/{id}/readings`
- Analysis: `POST /api/sessions/{id}/analyze-signal`, `GET /api/sessions/{id}/features`
- Assessment/history: `POST /api/sessions/{id}/assess-risk`, `GET /api/sessions/{id}/assessment`, `GET /api/history`

All errors have the shape `{ "error": { "code": "…", "message": "…" } }`.

## ESP32 pairing and ingestion

Register a device while logged in. The response returns `device_credential` once; store it securely on the device. Create a measurement session from the authenticated frontend, then post to:

```text
POST /api/devices/{registered-device-uuid}/readings
X-Device-Token: <device_credential>
```

The JSON body requires `session_id` and supports optional `device_id` (the registered `device_uid`), `timestamp`, `heart_rate`, `spo2`, `signal_quality`, and up to 2,048 raw `ppg` samples. Valid ingestion updates `last_seen`. The REST path is durable; the authenticated `/ws/sessions/{session_id}` endpoint is for validated live dashboard messages.

## Signal analysis and AI

`SignalAnalysisService` uses deterministic physiological calculations for this prototype and is intentionally isolated for a future PyTorch model. It calculates current HR statistics, RMSSD/HRV proxy, irregularity, personal-baseline deltas, and recent trends. If history is insufficient, baseline and trend values are null.

Set `AI_PROVIDER=mock` (default) for a fully local structured assessment. `base` and `finetuned` preserve the same validated response contract and safely use the mock behavior until a model runtime is connected. See [llm/README.md](llm/README.md) for the offline Unsloth integration layout. Model training never executes in an API handler.

## Tests

Run `python -m pytest -q`. Service tests cover baseline/trend calculations, mock assessment validation, and provider switching. API tests cover health and authentication/validation boundaries. The local container’s Python 3.14 + installed AnyIO combination hangs an in-process ASGI unauthorized-route test; run the suite under supported Python 3.11–3.13 for reliable API-client execution.
