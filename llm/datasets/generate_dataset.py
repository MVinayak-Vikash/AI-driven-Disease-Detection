"""
Synthetic Dataset Generator for Clinical Decision-Support Fine-Tuning.
Generates instruction-response pairs mapping multi-modal patient context,
symptoms, sensor metrics, baseline deviations, and longitudinal trends
into strict structured clinical risk assessments.
"""

import json
import random
from typing import List, Dict, Any

SYMPTOMS_POOL = [
    "chest_pain", "palpitations", "dizziness", "shortness_of_breath",
    "fatigue", "cold_sweats", "polydipsia", "polyuria", "lightheadedness",
    "blurred_vision", "pale_skin", "cold_extremities"
]

HISTORY_POOL = [
    "hypertension", "family_diabetes", "prior_cardiac_event",
    "iron_deficiency", "smoking", "chronic_kidney_disease"
]

SYSTEM_PROMPT = """You are an AI Clinical Early-Risk & Referral Navigator screening assistant.
Your role is to analyze multi-modal patient context, presenting symptoms, optical PPG sensor-derived features, personal baseline deviations, and longitudinal trends to produce an explainable early-risk assessment and specialist referral guidance.
Return strictly valid JSON adhering to the required clinical schema."""

def generate_sample(scenario_type: str) -> Dict[str, Any]:
    age = random.randint(22, 78)
    gender = random.choice(["male", "female"])

    if scenario_type == "high_cardiac":
        symptoms = random.sample(["chest_pain", "palpitations", "dizziness", "shortness_of_breath"], k=random.randint(2, 3))
        history = random.sample(["hypertension", "prior_cardiac_event", "smoking"], k=random.randint(1, 2))
        base_hr = random.randint(70, 78)
        curr_hr = random.randint(102, 130)
        base_hrv = random.randint(42, 52)
        curr_hrv = random.randint(14, 24)
        irreg = round(random.uniform(0.62, 0.88), 2)
        spo2 = random.randint(92, 96)
        sqi = round(random.uniform(0.88, 0.96), 2)

        hr_delta_pct = round(((curr_hr - base_hr) / base_hr) * 100.0, 1)
        hrv_delta_pct = round(((curr_hrv - base_hrv) / base_hrv) * 100.0, 1)

        input_context = {
            "patient": {"age": age, "gender": gender, "medical_history": history},
            "symptoms": symptoms,
            "current_sensor": {
                "heart_rate": curr_hr,
                "spo2": spo2,
                "hrv": curr_hrv,
                "rhythm_irregularity": irreg,
                "signal_quality": sqi
            },
            "baseline": {"has_baseline": True, "baseline_hr": base_hr, "baseline_hrv": base_hrv, "hr_delta_percent": hr_delta_pct, "hrv_delta_percent": hrv_delta_pct},
            "trend": {"has_trend": True, "hr_trend_direction": "increasing", "hrv_trend_direction": "decreasing"}
        }

        output_response = {
            "risk_level": "HIGH",
            "risk_score": round(random.uniform(78.0, 94.0), 1),
            "confidence": round(random.uniform(0.84, 0.92), 2),
            "conditions_of_concern": [
                {
                    "condition": "possible_abnormal_rhythm",
                    "risk": round(random.uniform(0.78, 0.92), 2),
                    "label": "Suspected Arrhythmia / Chaotic Depolarization",
                    "icdCode": "I48.91"
                }
            ],
            "evidence": [
                f"Heart rate elevated by +{hr_delta_pct}% from personal baseline ({base_hr} BPM)",
                f"HRV RMSSD suppressed by {hrv_delta_pct}% from personal baseline",
                f"Rhythm irregularity index elevated ({irreg})",
                f"Reported symptoms: {', '.join(symptoms)}"
            ],
            "trends": [
                "Progressive upward drift in resting heart rate across sessions",
                "Progressive autonomic HRV depression"
            ],
            "recommended_action": "Immediate 12-lead ECG and emergency physician evaluation.",
            "specialist": "Cardiology / Emergency Ward"
        }

    elif scenario_type == "moderate_metabolic_cardiac":
        symptoms = random.sample(["fatigue", "dizziness", "polydipsia"], k=2)
        history = random.sample(["hypertension", "family_diabetes"], k=1)
        base_hr = random.randint(72, 80)
        curr_hr = base_hr + random.randint(10, 18)
        base_hrv = random.randint(40, 48)
        curr_hrv = base_hrv - random.randint(8, 14)
        irreg = round(random.uniform(0.20, 0.40), 2)
        spo2 = random.randint(96, 99)
        sqi = round(random.uniform(0.90, 0.98), 2)

        hr_delta_pct = round(((curr_hr - base_hr) / base_hr) * 100.0, 1)
        hrv_delta_pct = round(((curr_hrv - base_hrv) / base_hrv) * 100.0, 1)

        input_context = {
            "patient": {"age": age, "gender": gender, "medical_history": history},
            "symptoms": symptoms,
            "current_sensor": {
                "heart_rate": curr_hr,
                "spo2": spo2,
                "hrv": curr_hrv,
                "rhythm_irregularity": irreg,
                "signal_quality": sqi
            },
            "baseline": {"has_baseline": True, "baseline_hr": base_hr, "baseline_hrv": base_hrv, "hr_delta_percent": hr_delta_pct, "hrv_delta_percent": hrv_delta_pct},
            "trend": {"has_trend": True, "hr_trend_direction": "increasing", "hrv_trend_direction": "decreasing"}
        }

        output_response = {
            "risk_level": "MODERATE",
            "risk_score": round(random.uniform(42.0, 62.0), 1),
            "confidence": round(random.uniform(0.78, 0.85), 2),
            "conditions_of_concern": [
                {
                    "condition": "cardiovascular_autonomic_stress",
                    "risk": round(random.uniform(0.48, 0.62), 2),
                    "label": "Cardiovascular Stress & Autonomic Strain",
                    "icdCode": "R00.8"
                }
            ],
            "evidence": [
                f"Moderate heart rate drift (+{hr_delta_pct}% above personal baseline)",
                f"Reduced HRV variability ({curr_hrv} ms)",
                f"Presenting symptoms: {', '.join(symptoms)}"
            ],
            "trends": [
                "Mild upward drift in heart rate relative to personal baseline"
            ],
            "recommended_action": "Schedule outpatient clinical checkup and continuous baseline tracking.",
            "specialist": "Cardiology / Internal Medicine"
        }

    else: # normal
        symptoms = []
        history = []
        base_hr = random.randint(66, 76)
        curr_hr = base_hr + random.randint(-4, 4)
        base_hrv = random.randint(45, 60)
        curr_hrv = base_hrv + random.randint(-5, 5)
        irreg = round(random.uniform(0.04, 0.12), 2)
        spo2 = random.randint(98, 100)
        sqi = round(random.uniform(0.92, 0.99), 2)

        hr_delta_pct = round(((curr_hr - base_hr) / base_hr) * 100.0, 1)
        hrv_delta_pct = round(((curr_hrv - base_hrv) / base_hrv) * 100.0, 1)

        input_context = {
            "patient": {"age": age, "gender": gender, "medical_history": history},
            "symptoms": symptoms,
            "current_sensor": {
                "heart_rate": curr_hr,
                "spo2": spo2,
                "hrv": curr_hrv,
                "rhythm_irregularity": irreg,
                "signal_quality": sqi
            },
            "baseline": {"has_baseline": True, "baseline_hr": base_hr, "baseline_hrv": base_hrv, "hr_delta_percent": hr_delta_pct, "hrv_delta_percent": hrv_delta_pct},
            "trend": {"has_trend": True, "hr_trend_direction": "stable", "hrv_trend_direction": "stable"}
        }

        output_response = {
            "risk_level": "LOW",
            "risk_score": round(random.uniform(6.0, 18.0), 1),
            "confidence": round(random.uniform(0.88, 0.95), 2),
            "conditions_of_concern": [
                {
                    "condition": "normative_sinus_dynamics",
                    "risk": 0.08,
                    "label": "Normative Sinus Rhythm",
                    "icdCode": "Z00.00"
                }
            ],
            "evidence": [
                f"Resting heart rate ({curr_hr} BPM) perfectly aligned with personal baseline ({base_hr} BPM)",
                "Robust autonomic HRV variability",
                "Zero acute clinical symptoms reported"
            ],
            "trends": [
                "Stable longitudinal baseline across sessions"
            ],
            "recommended_action": "Maintain routine wellness screening.",
            "specialist": "Primary Care / General Wellness"
        }

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze the following patient and physiological sensor context and return strict JSON:\n{json.dumps(input_context, indent=2)}"},
            {"role": "assistant", "content": json.dumps(output_response, indent=2)}
        ]
    }

def main():
    samples = []
    scenarios = ["high_cardiac", "moderate_metabolic_cardiac", "normal"]
    
    for _ in range(150):
        sc = random.choice(scenarios)
        samples.append(generate_sample(sc))

    output_path = "llm/datasets/sample_training_dataset.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")
            
    print(f"Generated {len(samples)} training samples at '{output_path}'.")

if __name__ == "__main__":
    main()
