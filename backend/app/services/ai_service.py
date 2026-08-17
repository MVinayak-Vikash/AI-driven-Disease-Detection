import json
import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx

from backend.app.core.config import settings
from backend.app.schemas.assessment import LLMStructuredInput, AIAssessmentResponse

logger = logging.getLogger("cardionav.ai_service")

CLINICAL_SYSTEM_PROMPT = """You are an AI Clinical Early-Risk & Referral Navigator screening assistant.
Your role is to analyze multi-modal patient context, presenting symptoms, optical PPG sensor-derived features, personal baseline deviations, and longitudinal trends to produce an explainable early-risk assessment and specialist referral guidance.

CRITICAL CLINICAL & SAFETY DIRECTIVES:
1. This system is strictly an EARLY-RISK SCREENING and CLINICAL DECISION-SUPPORT prototype.
2. DO NOT claim to definitively diagnose disease or replace physician examination.
3. Use ONLY the provided evidence: patient demographics, medical history, reported symptoms, current sensor measurements, personal baseline, and trend deltas.
4. NEVER invent symptoms, measurements, history, or laboratory results not provided in the input.
5. Explicitly communicate confidence and uncertainty. When evidence is limited or normal, confidence should reflect that.
6. When physiological features deviate significantly from the personal baseline (e.g. elevated HR delta, depressed HRV delta), cite this baseline shift in the evidence.
7. Return ONLY a valid JSON object matching the exact schema below, with NO extra markdown text or conversational filler.

REQUIRED JSON SCHEMA:
{
  "risk_level": "LOW | MODERATE | HIGH",
  "risk_score": 0.0 to 100.0,
  "confidence": 0.0 to 1.0,
  "conditions_of_concern": [
    {
      "condition": "string",
      "risk": 0.0 to 1.0,
      "label": "string",
      "icdCode": "string"
    }
  ],
  "evidence": ["string"],
  "trends": ["string"],
  "recommended_action": "string",
  "specialist": "string"
}
"""

def build_prompt_payload(input_data: LLMStructuredInput) -> str:
    """Builds the serialized context string for LLM inference."""
    return json.dumps(input_data.model_dump(), indent=2)

def sanitize_json_response(raw_text: str) -> Dict[str, Any]:
    """Safely extracts JSON object from raw LLM output."""
    raw_text = raw_text.strip()
    
    # Try direct parse
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # Extract JSON inside markdown code block
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Extract outermost braces
    brace_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from LLM output")

class AIAssessmentService(ABC):
    """Abstract base class for all AI assessment providers."""
    
    @abstractmethod
    async def assess(self, session_id: str, input_data: LLMStructuredInput) -> AIAssessmentResponse:
        pass

class MockAIService(AIAssessmentService):
    """
    Deterministic Mock AI Reasoning Service.
    Evaluates patient demographics, symptoms, sensor metrics, 
    baseline shifts, and longitudinal trends to produce realistic risk evaluations.
    """

    async def assess(self, session_id: str, input_data: LLMStructuredInput) -> AIAssessmentResponse:
        pt = input_data.patient
        sensor = input_data.current_sensor
        symptoms = [s.lower() for s in input_data.symptoms]
        history = [h.lower() for h in pt.medical_history]
        baseline = input_data.baseline
        trend = input_data.trend

        hr = sensor.heart_rate or 72.0
        hrv = sensor.hrv or 45.0
        rhythm_irreg = sensor.rhythm_irregularity or 0.08
        spo2 = sensor.spo2 or 98.0

        evidence: List[str] = []
        trends_list: List[str] = []
        conditions: List[Dict[str, Any]] = []

        # Baseline evaluation
        hr_elevated_from_baseline = False
        hrv_depressed_from_baseline = False

        if baseline and baseline.get("has_baseline"):
            base_hr = baseline.get("baseline_hr")
            base_hrv = baseline.get("baseline_hrv")
            hr_delta_pct = baseline.get("hr_delta_percent", 0.0)
            hrv_delta_pct = baseline.get("hrv_delta_percent", 0.0)

            if hr_delta_pct > 15.0:
                hr_elevated_from_baseline = True
                evidence.append(f"Heart rate is elevated by +{hr_delta_pct:.1f}% relative to personal baseline ({base_hr} BPM)")
            if hrv_delta_pct < -20.0:
                hrv_depressed_from_baseline = True
                evidence.append(f"HRV RMSSD is reduced by {hrv_delta_pct:.1f}% relative to personal baseline ({base_hrv} ms)")
        else:
            trends_list.append("Longitudinal personal baseline not yet established (first/early recording session)")

        # Trend trajectory evaluation
        if trend and trend.get("has_trend"):
            hr_dir = trend.get("hr_trend_direction")
            hrv_dir = trend.get("hrv_trend_direction")
            if hr_dir == "increasing":
                trends_list.append("Longitudinal telemetry shows upward drift in resting heart rate across sessions")
            if hrv_dir == "decreasing":
                trends_list.append("Longitudinal telemetry indicates progressive downward trend in autonomic HRV")

        # Clinical Risk Scoring Calculation
        risk_points = 0.0

        # Sensor-derived factors
        if rhythm_irreg >= 0.50:
            risk_points += 35.0
            evidence.append(f"Elevated rhythm irregularity index ({rhythm_irreg:.2f}) indicating irregular inter-beat intervals")
            conditions.append({
                "condition": "possible_abnormal_rhythm",
                "risk": round(min(0.95, 0.45 + rhythm_irreg * 0.4), 2),
                "label": "Suspected Cardiac Arrhythmia / Atrial Irregularity",
                "icdCode": "I48.91"
            })
        elif rhythm_irreg >= 0.20:
            risk_points += 15.0
            evidence.append(f"Mild pulse interval variance detected ({rhythm_irreg:.2f})")

        if hr >= 100.0:
            risk_points += 20.0
            evidence.append(f"Resting tachycardia observed ({hr:.0f} BPM)")
        elif hr <= 50.0:
            risk_points += 15.0
            evidence.append(f"Resting bradycardia observed ({hr:.0f} BPM)")

        if hrv < 25.0:
            risk_points += 15.0
            evidence.append(f"Depressed heart rate variability ({hrv:.1f} ms) reflecting autonomic nervous strain")

        if spo2 < 95.0:
            risk_points += 15.0
            evidence.append(f"Peripheral oxygen saturation below nominal threshold ({spo2:.0f}% SpO2)")
            conditions.append({
                "condition": "hypoxemic_stress",
                "risk": 0.65,
                "label": "Sub-optimal Oxygen Saturation",
                "icdCode": "R09.02"
            })

        # Symptom factors
        if "chest_pain" in symptoms or "chest_discomfort" in symptoms:
            risk_points += 35.0
            evidence.append("Patient reported acute chest discomfort or pressure")
        if "palpitations" in symptoms:
            risk_points += 15.0
            evidence.append("Patient reported rapid fluttering or palpitations")
        if "dizziness" in symptoms or "lightheadedness" in symptoms:
            risk_points += 12.0
            evidence.append("Patient reported dizziness / postural lightheadedness")
        if "fatigue" in symptoms:
            risk_points += 8.0
            evidence.append("Patient reported persistent fatigue")

        # History factors
        if "hypertension" in history:
            risk_points += 10.0
            evidence.append("Prior history of hypertension / elevated vascular resistance")
        if "prior_cardiac_event" in history:
            risk_points += 15.0
            evidence.append("Known clinical history of prior cardiovascular event")

        # Determine Triage Level and Recommendations
        if risk_points >= 50.0 or rhythm_irreg >= 0.60 or "chest_pain" in symptoms:
            risk_level = "HIGH"
            risk_score = min(96.0, max(65.0, risk_points))
            confidence = 0.86
            recommended_action = "Urgent clinical evaluation and 12-lead ECG telemetry recommended."
            specialist = "Cardiology / Emergency Ward"
        elif risk_points >= 25.0 or hr_elevated_from_baseline or hrv_depressed_from_baseline:
            risk_level = "MODERATE"
            risk_score = min(64.0, max(30.0, risk_points))
            confidence = 0.80
            recommended_action = "Schedule non-urgent outpatient consultation and monitor baseline trends."
            specialist = "Cardiology / General Internal Medicine"
        else:
            risk_level = "LOW"
            risk_score = max(5.0, min(24.0, risk_points if risk_points > 0 else 10.0))
            confidence = 0.90
            recommended_action = "Measurements within normative parameters. Continue routine screening."
            specialist = "Primary Care / Wellness"
            if not evidence:
                evidence.append("Normative pulse rhythm and heart rate metrics within healthy reference range")

        if not conditions:
            conditions.append({
                "condition": "normative_sinus_dynamics" if risk_level == "LOW" else "cardiovascular_stress",
                "risk": round(risk_score / 100.0, 2),
                "label": "Nominal Physiological Profile" if risk_level == "LOW" else "Cardiovascular Stress Pattern",
                "icdCode": "Z00.00" if risk_level == "LOW" else "R00.8"
            })

        return AIAssessmentResponse(
            session_id=session_id,
            risk_level=risk_level,
            risk_score=round(risk_score, 1),
            confidence=round(confidence, 2),
            conditions_of_concern=conditions,
            evidence=evidence,
            trends=trends_list,
            recommended_action=recommended_action,
            specialist=specialist,
            model_name="mock-cardionav-reasoner",
            model_version="1.0.0-mock",
            raw_response={"provider": "mock", "risk_points": risk_points}
        )

class BaseModelAIService(AIAssessmentService):
    """
    Calls open-source instruct models via OpenAI-compatible endpoints
    (e.g., Together AI, vLLM, Ollama, Groq).
    """

    def __init__(self, model_name: str, base_url: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or "sk-placeholder"

    async def assess(self, session_id: str, input_data: LLMStructuredInput) -> AIAssessmentResponse:
        user_content = build_prompt_payload(input_data)
        messages = [
            {"role": "system", "content": CLINICAL_SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze the following patient and physiological sensor context and return strict JSON:\n{user_content}"}
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 700,
            "response_format": {"type": "json_object"} if "openai" in self.base_url else None
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                parsed = sanitize_json_response(content)

                return AIAssessmentResponse(
                    session_id=session_id,
                    risk_level=parsed.get("risk_level", "MODERATE"),
                    risk_score=float(parsed.get("risk_score", 50.0)),
                    confidence=float(parsed.get("confidence", 0.75)),
                    conditions_of_concern=parsed.get("conditions_of_concern", []),
                    evidence=parsed.get("evidence", []),
                    trends=parsed.get("trends", []),
                    recommended_action=parsed.get("recommended_action", "Clinical evaluation recommended"),
                    specialist=parsed.get("specialist", "Internal Medicine"),
                    model_name=self.model_name,
                    model_version="instruct-base",
                    raw_response=parsed
                )
        except Exception as e:
            logger.warning(f"BaseModelAIService request failed: {e}. Falling back to MockAIService.")
            mock_fallback = MockAIService()
            res = await mock_fallback.assess(session_id, input_data)
            res.model_name = f"{self.model_name}-fallback"
            return res

class FineTunedLLMService(AIAssessmentService):
    """
    Executes fine-tuned Unsloth / Hugging Face model checkpoint.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self._load_model_safe()

    def _load_model_safe(self):
        try:
            from unsloth import FastLanguageModel
            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_path,
                max_seq_length=2048,
                load_in_4bit=True
            )
            FastLanguageModel.for_inference(self.model)
            logger.info(f"Loaded Unsloth model successfully from {self.model_path}")
        except Exception as e:
            logger.info(f"Unsloth runtime model not available at '{self.model_path}': {e}. Using deterministic fallback.")
            self.model = None

    async def assess(self, session_id: str, input_data: LLMStructuredInput) -> AIAssessmentResponse:
        if not self.model or not self.tokenizer:
            mock = MockAIService()
            res = await mock.assess(session_id, input_data)
            res.model_name = "unsloth-finetuned-emulated"
            return res

        # Run local generation
        import torch
        prompt_text = f"{CLINICAL_SYSTEM_PROMPT}\n\nPatient Context:\n{build_prompt_payload(input_data)}\n\nResponse (JSON):"
        inputs = self.tokenizer([prompt_text], return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
        outputs = self.model.generate(**inputs, max_new_tokens=600, temperature=0.1, use_cache=True)
        raw_output = self.tokenizer.batch_decode(outputs)[0]

        try:
            parsed = sanitize_json_response(raw_output)
            return AIAssessmentResponse(
                session_id=session_id,
                risk_level=parsed.get("risk_level", "MODERATE"),
                risk_score=float(parsed.get("risk_score", 50.0)),
                confidence=float(parsed.get("confidence", 0.85)),
                conditions_of_concern=parsed.get("conditions_of_concern", []),
                evidence=parsed.get("evidence", []),
                trends=parsed.get("trends", []),
                recommended_action=parsed.get("recommended_action", "Clinical evaluation recommended"),
                specialist=parsed.get("specialist", "Cardiology"),
                model_name="cardionav-unsloth-lora",
                model_version="1.0.0-lora",
                raw_response=parsed
            )
        except Exception as e:
            logger.warning(f"Failed to parse Unsloth output: {e}. Falling back.")
            mock = MockAIService()
            return await mock.assess(session_id, input_data)

def get_ai_service(provider: Optional[str] = None) -> AIAssessmentService:
    """
    Factory function returning the active AI assessment service implementation.
    """
    prov = (provider or settings.AI_PROVIDER).lower().strip()
    if prov == "base":
        return BaseModelAIService(
            model_name=settings.MODEL_NAME,
            base_url=settings.MODEL_BASE_URL or "https://api.together.xyz/v1",
            api_key=settings.MODEL_API_KEY
        )
    elif prov == "finetuned":
        return FineTunedLLMService(model_path=settings.UNSLOTH_MODEL_PATH or "./llm/checkpoints")
    else:
        return MockAIService()
