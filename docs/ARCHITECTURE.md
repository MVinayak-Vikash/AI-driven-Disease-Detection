# 🏛️ CardioNav AI — System Architecture

CardioNav AI is an explainable **Clinical Early-Risk Screening and Decision-Support Platform**. It couples low-cost ESP32 optical photoplethysmography (PPG) sensors with multi-tiered AI reasoning to detect elevated cardiovascular, metabolic, and hemodynamic risk patterns and provide specialist referral recommendations.

---

## 🏗️ End-to-End System Topology

```
+-----------------------------------------------------------------------------------+
|                                 USER / CLINICIAN                                  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        SUPABASE AUTHENTICATION (JWT)                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                         FRONTEND (Next.js / HTML5)                                |
|  - Real-time 60 FPS PPG Waveform Canvas                                           |
|  - Patient Demographics & Intake Form                                            |
|  - Multi-Disease Risk Prediction Cards & Referral Triage                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|                                                                                   |
|  +---------------------------+       +-----------------------------------------+  |
|  |     Supabase Database     |       |           Device Management             |  |
|  |  PostgreSQL + Strict RLS  |       |  Multi-ESP32 per user + Token Hashing   |  |
|  +---------------------------+       +-----------------------------------------+  |
|                                                                                   |
|  +---------------------------+       +-----------------------------------------+  |
|  |     Sensor Ingestion      |       |      Real-Time WebSocket Stream         |  |
|  |  Range validation & store |       |   Live PPG waveform frame broadcast     |  |
|  +---------------------------+       +-----------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                 LAYER 1: PHYSIOLOGICAL SIGNAL MODEL                         |  |
|  |  - Bandpass filtering & Systolic peak detection                             |  |
|  |  - Mean / Min / Max Heart Rate                                              |  |
|  |  - HRV (SDNN) & RMSSD Autonomic Variance                                    |  |
|  |  - Rhythm Irregularity Index (Arrhythmia detection)                         |  |
|  |  - Signal Quality Index (SQI)                                               |  |
|  |  - Personal Baseline & Longitudinal Trend Deltas                            |  |
|  |  - Zero scikit-learn dependency; PyTorch extensible interface               |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                 LAYER 2: MULTI-MODAL AI REASONING                           |  |
|  |  - Abstract AIAssessmentService provider architecture                       |  |
|  |  - Providers: Mock (Rule-based), Base LLM, Fine-Tuned Unsloth LoRA          |  |
|  |  - Strict Pydantic JSON Schema Validation & Error Recovery Fallback         |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
         ^                                                                |
         | (WiFi REST / Token Auth)                                       v
+------------------+                                            +-------------------+
|  ESP32 Hardware  |                                            |   AI ASSESSMENT   |
|     MAX30102     |                                            | Triage & Referral |
+------------------+                                            +-------------------+
```

---

## 🔬 Two-Tier AI Architecture

### Layer 1 — Physiological Signal Analysis
- **Purpose**: Transform high-frequency, noisy optical PPG waveforms into verified physiological biomarkers.
- **Inputs**: Raw PPG arrays, timestamps, instantaneous BPM, SpO2.
- **Outputs**: `heart_rate_mean`, `hrv`, `rmssd`, `rhythm_irregularity`, `signal_quality`, `baseline_delta`, `trend_delta`.
- **Implementation**: Pure NumPy and mathematical peak-detection algorithms designed to run with zero dependencies or be replaced by a PyTorch learned model.

### Layer 2 — Multi-Modal Clinical Decision-Support Reasoner
- **Purpose**: Contextualize sensor metrics within patient history, age, biological sex, presenting symptoms, and baseline shifts.
- **Inputs**: Structured JSON combining demographics, symptoms, sensor metrics, and longitudinal deltas.
- **Outputs**: Clinical early-risk level (`LOW`, `MODERATE`, `HIGH`), risk score (0-100), confidence (0.0-1.0), explainable evidence points, trend insights, recommended clinical actions, and target specialist ward referral.
- **Providers**:
  - `MockAIService`: Instant zero-dependency development fallback with high clinical realism.
  - `BaseModelAIService`: Interfaces with standard open-weight instruct models via OpenAI-compatible endpoints.
  - `FineTunedLLMService`: Local GPU inference using Unsloth 4-bit LoRA checkpoints.
