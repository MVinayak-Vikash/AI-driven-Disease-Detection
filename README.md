# 🫀 CardioNav AI — AI Early-Risk & Referral Navigator

> **Clinical Decision-Support Screening Prototype**: A multi-modal clinical screening platform pairing real-time optical photoplethysmography (PPG) from low-cost ESP32 MAX30102 sensors with two-layer AI reasoning (signal analytics + fine-tuned LLMs) to provide early-risk triage and specialist referral guidance.

---

## ⚡ Key Highlights & Architecture
- **Supabase Integration**: Auth, PostgreSQL with Row Level Security (RLS) policies on all tables (`profiles`, `devices`, `measurement_sessions`, `sensor_readings`, `physiological_features`, `ai_assessments`).
- **Hardware Integration**: ESP32 + MAX30102 with secure hardware token authentication (no exposed service role keys).
- **Two-Layer AI Reasoning**:
  - **Layer 1 (Signal Analysis)**: PPG filtering, peak detection, mean/min/max HR, HRV (SDNN), RMSSD, rhythm irregularity index, and signal quality index (SQI). Zero scikit-learn dependency.
  - **Layer 2 (Clinical Decision Support)**: Synthesizes demographics, symptoms, sensor metrics, and longitudinal baseline deviations to generate explainable evidence chains and referral actions.
- **Provider Agnostic**: Switch seamlessly between `AI_PROVIDER=mock`, `AI_PROVIDER=base`, and `AI_PROVIDER=finetuned`.
- **Longitudinal Sensitivity**: Tracks personal baseline shifts and trends across recording sessions rather than relying on static population cutoffs.

---

## 📁 Repository Structure
```
├── backend/
│   ├── app/
│   │   ├── core/         # Config, JWT security, Supabase database client
│   │   ├── schemas/      # Pydantic validation schemas
│   │   ├── services/     # Device, Sensor, Signal, Baseline, & AI services
│   │   ├── api/routes/   # REST & WebSocket endpoints
│   │   └── main.py       # FastAPI application entry point
│   └── tests/            # Automated pytest test suites
├── supabase/
│   └── migrations/       # PostgreSQL DDL, foreign keys, indexes, and RLS policies
├── llm/
│   ├── datasets/         # Synthetic dataset generator & sample training data
│   ├── training/         # Unsloth 4-bit LoRA fine-tuning script & guide
│   └── inference/        # Standalone inference runner
├── firmware/
│   └── esp32/            # ESP32 + MAX30102 Arduino C++ firmware
├── frontend/             # Real-time PPG canvas, intake forms, & decision UI
├── docs/                 # API, Architecture, & Deployment guides
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

---

## 🚀 Quick Start Guide

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Run FastAPI Backend
```bash
uvicorn backend.app.main:app --port 8000 --reload
```
API Documentation will be live at `http://localhost:8000/docs`.

### 4. Run Automated Verification Tests
```bash
pytest backend/tests/ -v
```

### 5. Launch Frontend
Open `frontend/index.html` in any modern web browser or serve locally:
```bash
python frontend/server.py
```

---

## 🔒 Clinical & Safety Disclaimer
*CardioNav AI is strictly an early-risk screening and clinical decision-support prototype. It does not provide definitive medical diagnoses and is intended to assist healthcare providers in triage and specialist referral.*
