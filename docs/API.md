# 📡 CardioNav AI — REST & WebSocket API Specification

## Base URL
- Local: `http://localhost:8000`
- Production: `https://your-api-domain.com`

---

## 🔒 Authentication
All user endpoints require a Supabase JWT in the `Authorization` header:
```http
Authorization: Bearer <supabase_access_token>
```
ESP32 Hardware Ingestion endpoints authenticate using the `X-Device-Token` header:
```http
X-Device-Token: <generated_device_token>
```

---

## 📋 Endpoints Overview

### 1. System & Authentication
- `GET /health` — Returns system status, version, and active `AI_PROVIDER`.
- `GET /api/me` — Returns authenticated Supabase user profile claims.

### 2. Patient Profile
- `GET /api/profile` — Retrieves patient demographics and medical history.
- `PUT /api/profile` — Updates patient name, age, gender, and comorbidities.

### 3. ESP32 Device Management
- `POST /api/devices` — Registers a new ESP32 sensor (returns `generated_token`).
- `GET /api/devices` — Lists all devices registered to the user.
- `GET /api/devices/{device_id}` — Gets single device details.
- `DELETE /api/devices/{device_id}` — Deletes/unregisters a device.

### 4. Measurement Sessions
- `POST /api/sessions` — Starts a new screening measurement session.
- `GET /api/sessions` — Lists all historical sessions for the user.
- `GET /api/sessions/{session_id}` — Gets metadata for a specific session.
- `POST /api/sessions/{session_id}/finish` — Concludes the recording session.

### 5. Sensor Telemetry Ingestion
- `POST /api/devices/{device_id}/readings` — Hardware ingestion endpoint for ESP32.
- `POST /api/sessions/{session_id}/readings` — Ingests a reading into a specific session.
- `GET /api/sessions/{session_id}/readings` — Retrieves all sensor readings for a session.

### 6. Signal Analysis & Feature Extraction (Layer 1)
- `POST /api/sessions/{session_id}/analyze-signal` — Computes HR mean/min/max, HRV (SDNN), RMSSD, rhythm irregularity index, SQI, and personal baseline deltas.
- `GET /api/sessions/{session_id}/features` — Retrieves computed physiological features.

### 7. AI Clinical Decision Support (Layer 2)
- `POST /api/sessions/{session_id}/assess-risk` — Executes multimodal AI risk assessment synthesizing patient history, symptoms, sensor metrics, and longitudinal trends.
- `GET /api/sessions/{session_id}/assessment` — Retrieves existing AI assessment for a session.

### 8. Longitudinal Screening History
- `GET /api/history` — Lists all past screening records with computed features and assessments.
- `GET /api/history/{session_id}` — Detailed report for a single historical session.

### 9. Real-Time Telemetry Streaming
- `WS /ws/sessions/{session_id}` — Live bidirectional stream of raw PPG waveforms and BPM.
