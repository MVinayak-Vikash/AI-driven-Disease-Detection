# 🫀 CardioNav AI — AI Early-Risk & Referral Navigator
### VITSIH-26: AI-Powered Early Disease Detection & Clinical Referral Decision-Support Platform

> **Clinical Decision Support Prototype**: A multi-modal screening platform that captures real-time physiological signals from low-cost ESP32 PPG sensors, extracts rhythm and hemodynamic features, and pairs them with patient symptoms and clinical history using fine-tuned LLM reasoning to produce explainable risk assessments and specialist referral guidance.

---

## 🌟 Quick Start Guide (Run in Any Browser)

### Method 1: Instant Python Server (Recommended)
Open your terminal in this folder and run:
```bash
python server.py
```
This will automatically launch the server and open **`http://localhost:5173`** in your default browser. It also includes built-in mock endpoints for `/health`, `/api/sensor/ppg`, and `/api/assess`.

### Method 2: Direct Double-Click
You can double-click **`index.html`** to open it directly in Google Chrome, Microsoft Edge, Mozilla Firefox, or Apple Safari!

---

## 🚀 How to Host & Send a Live Link to Judges (3 Free Options)

When you need to share a live URL with hackathon evaluators or teammates:

### Option A: Netlify Drop (Easiest — 30 Seconds, No Git Required)
1. Go to **[app.netlify.com/drop](https://app.netlify.com/drop)**.
2. Drag and drop the `VITSIH-26` folder onto the web page.
3. You will instantly get a live public HTTPS link (e.g. `https://cardionav-vitsih26.netlify.app`) that works on all computers, tablets, and phones!

### Option B: GitHub Pages
1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "CardioNav AI Frontend Complete"
   git branch -M main
   git remote add origin https://github.com/<your-username>/cardionav-ai.git
   git push -u origin main
   ```
2. Go to your repo **Settings** ➔ **Pages** ➔ Set Branch to **`main`** ➔ Save.
3. Your site will be live at `https://<your-username>.github.io/cardionav-ai/`.

### Option C: Vercel
1. Install Vercel CLI or import via GitHub on **[vercel.com](https://vercel.com)**.
2. Deploy with default settings to get a live `.vercel.app` URL.

---

## 👥 4-Person Hackathon Team Division & API Contracts

This frontend is designed so that you (Person 3) and all 3 of your teammates can work in parallel without blocking each other:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ Person 1        │       │ Person 2        │       │ Person 3        │       │ Person 4        │
│ Signal / ML     │       │ LLM Reasoning   │       │ Frontend (You)  │       │ Backend / API   │
│ • PPG filtering │       │ • Unsloth / LLM │       │ • 60 FPS Canvas │       │ • FastAPI / WS  │
│ • Peak detect   │       │ • Prompt format │       │ • Patient form  │       │ • ESP32 bridge  │
│ • HR & HRV      │       │ • Strict JSON   │       │ • Decision UI   │       │ • Endpoints     │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 1. Hardware & Sensor API Contract (Person 4 Backend & Person 1 ML)
- **REST Endpoint**: `POST /api/sensor/ppg`
```json
{
  "device_id": "ESP32_01",
  "timestamp": 1723789200,
  "bpm": 108,
  "spo2": 96,
  "signal": [124, 130, 142, 160, 185, 170, 140, 120]
}
```
- **WebSocket Endpoint**: `ws://localhost:8000/ws/sensor` (streams live raw values to the canvas).

### 2. Clinical AI Reasoning Contract (Person 2 LLM & Person 4 Backend)
- **REST Endpoint**: `POST /api/assess`
- **Request Payload**:
```json
{
  "patient": {
    "name": "Vikram Sundaram",
    "age": 52,
    "sex": "male",
    "bp_systolic": 148,
    "bp_diastolic": 92
  },
  "symptoms": ["palpitations", "dizziness", "fatigue"],
  "history": ["hypertension", "smoking"],
  "sensor": {
    "heart_rate": 108,
    "hrv": 21.4,
    "rhythm_irregularity": 0.76,
    "signal_quality": 0.93,
    "spo2": 96
  }
}
```
- **Expected LLM Structured JSON Response (Section 5 & 11 Contract)**:
```json
{
  "risk_level": "HIGH",
  "risk_score_numeric": 78,
  "conditions_of_concern": [
    {
      "condition": "possible_arrhythmia",
      "label": "Suspected Atrial Fibrillation / Rhythm Irregularity",
      "risk": 0.78,
      "icdCode": "I48.91"
    }
  ],
  "evidence": [
    "Elevated resting heart rate (108 BPM)",
    "Marked RR-interval irregularity index (76%)",
    "Reported palpitations and dizziness",
    "Stage 1/2 Hypertensive BP profile (148/92 mmHg)"
  ],
  "confidence": 0.81,
  "recommended_action": "physician_evaluation",
  "specialist": "cardiology",
  "urgency_tier": "Urgent: Cardiology Consult within 24-48h",
  "clinical_summary": "Screening analysis indicates a HIGH risk profile driven by suspected arrhythmia with irregular pulse dynamics..."
}
```

---

## 🎯 2-Minute Hackathon Demo Script

Follow this sequence when presenting to judges:

1. **The Hook (30 sec)**:
   > *"Millions of cardiac cases are diagnosed too late because patients dismiss subtle symptoms and lack access to immediate specialist screening. CardioNav AI turns low-cost ESP32 optical sensors into an explainable clinical decision-support station."*

2. **Demonstrate High-Risk Patient (45 sec)**:
   - Click the top demo preset: `🔴 52yo Male - Suspected Arrhythmia / AFib (High Risk)`.
   - Point out the **real-time 60 FPS PPG waveform** with erratic systolic peaks and the irregularity index jumping to `0.76`.
   - Click **Run Multimodal AI Clinical Risk Assessment**.
   - Show the **High Risk Badge**, the **81% Confidence Gauge**, the **Multimodal Evidence Chain**, and the automated referral to **Department of Cardiology**.

3. **Demonstrate Low-Risk Screening (30 sec)**:
   - Switch to `🟢 28yo Female - Normal Sinus Rhythm (Low Risk)`.
   - Show how the waveform normalizes with a crisp dicrotic notch, and the system triages them as `Low Risk: Routine Annual Screening`.

4. **Show Clinical Brief & Telemetry (15 sec)**:
   - Click **Clinical Brief** to show the printable triage report with hospital stamp lines and QR verification.
   - Click **Pipeline Telemetry** to show judges the underlying 5-stage edge-to-AI pipeline and strict JSON schema contract!

---

## 📋 Hackathon Compliance & Safety Disclaimer
*CardioNav AI is built strictly as a clinical screening and decision-support prototype. It does not replace definitive medical diagnosis and requires formal physician validation.*
