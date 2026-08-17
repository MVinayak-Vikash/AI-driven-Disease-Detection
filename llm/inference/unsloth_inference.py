"""
Standalone Unsloth Inference Script for Clinical Decision Support.
Tests model generation and validates structured output.
"""

import json
import argparse
from typing import Dict, Any

def run_inference(model_path: str, input_json_str: str) -> Dict[str, Any]:
    try:
        from unsloth import FastLanguageModel
        import torch
    except ImportError:
        print("Unsloth is not installed. To run inference, install unsloth.")
        return {}

    print(f"Loading model checkpoint from {model_path}...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=2048,
        load_in_4bit=True
    )
    FastLanguageModel.for_inference(model)

    system_prompt = "You are an AI Clinical Early-Risk & Referral Navigator screening assistant. Return strictly valid JSON."
    prompt = f"{system_prompt}\n\nPatient Context:\n{input_json_str}\n\nResponse (JSON):"

    inputs = tokenizer([prompt], return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
    outputs = model.generate(**inputs, max_new_tokens=600, temperature=0.1, use_cache=True)
    raw_output = tokenizer.batch_decode(outputs)[0]

    print("\n" + "=" * 60)
    print("RAW MODEL OUTPUT:")
    print("=" * 60)
    print(raw_output)
    print("=" * 60)
    return {"raw": raw_output}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, default="../checkpoints/cardionav-unsloth-lora")
    args = parser.parse_args()

    sample_context = json.dumps({
        "patient": {"age": 54, "gender": "male", "medical_history": ["hypertension", "smoking"]},
        "symptoms": ["chest_pain", "palpitations"],
        "current_sensor": {"heart_rate": 112, "spo2": 95, "hrv": 18.5, "rhythm_irregularity": 0.78, "signal_quality": 0.94},
        "baseline": {"has_baseline": True, "baseline_hr": 74, "baseline_hrv": 46, "hr_delta_percent": 51.3, "hrv_delta_percent": -59.7},
        "trend": {"has_trend": True, "hr_trend_direction": "increasing", "hrv_trend_direction": "decreasing"}
    }, indent=2)

    run_inference(args.model_path, sample_context)
