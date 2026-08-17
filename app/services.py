from __future__ import annotations
from collections.abc import Sequence
from statistics import mean
from typing import Any
import math
from .schemas import AssessmentOutput


class SignalAnalysisService:
    """Deterministic fallback; isolated so a PyTorch model can replace it later."""
    def analyze(self, readings: Sequence[dict], historical: Sequence[dict]) -> dict:
        hrs = [float(r["heart_rate"]) for r in readings if r.get("heart_rate") is not None]
        qualities = [float(r["signal_quality"]) for r in readings if r.get("signal_quality") is not None]
        if not hrs:
            raise ValueError("At least one heart-rate reading is required for analysis")
        hr_mean = mean(hrs)
        diffs = [hrs[i] - hrs[i - 1] for i in range(1, len(hrs))]
        hrv = math.sqrt(mean([d * d for d in diffs])) if diffs else 0.0
        rmssd = hrv
        irregularity = min(1.0, hrv / max(hr_mean, 1.0))
        feature = {"heart_rate_mean": hr_mean, "heart_rate_min": min(hrs), "heart_rate_max": max(hrs), "hrv": hrv, "rmssd": rmssd, "rhythm_irregularity": irregularity, "signal_quality": mean(qualities) if qualities else None}
        previous = [h for h in historical if h.get("heart_rate_mean") is not None]
        if not previous:
            feature["baseline_delta"] = None
            feature["trend_delta"] = None
            return feature
        baseline_hr = mean([float(x["heart_rate_mean"]) for x in previous])
        baseline_hrv_values = [float(x["hrv"]) for x in previous if x.get("hrv") is not None]
        baseline_hrv = mean(baseline_hrv_values) if baseline_hrv_values else 0.0
        feature["baseline_delta"] = {"heart_rate_baseline": baseline_hr, "heart_rate_delta_percent": percent_change(hr_mean, baseline_hr), "hrv_baseline": baseline_hrv, "hrv_delta_percent": percent_change(hrv, baseline_hrv) if baseline_hrv else None}
        if len(previous) < 2:
            feature["trend_delta"] = None
        else:
            recent = previous[-min(3, len(previous)):]
            first, last = recent[0], recent[-1]
            feature["trend_delta"] = {"heart_rate_delta_percent": percent_change(hr_mean, float(first["heart_rate_mean"])), "historical_heart_rate_delta_percent": percent_change(float(last["heart_rate_mean"]), float(first["heart_rate_mean"]))}
        return feature


def percent_change(current: float, baseline: float) -> float:
    return round(((current - baseline) / baseline) * 100, 2) if baseline else 0.0


class BaseAIAssessmentService:
    async def assess(self, payload: dict[str, Any]) -> AssessmentOutput: raise NotImplementedError


class MockAIService(BaseAIAssessmentService):
    async def assess(self, payload: dict[str, Any]) -> AssessmentOutput:
        sensor, baseline, symptoms = payload["current_sensor"], payload.get("baseline") or {}, payload.get("symptoms", [])
        score, evidence, trends = 0.12, [], []
        if sensor.get("heart_rate", 0) >= 100: score += .28; evidence.append("heart rate is elevated in this measurement")
        if sensor.get("rhythm_irregularity", 0) >= .15: score += .22; evidence.append("rhythm irregularity indicator is elevated")
        if baseline.get("heart_rate_delta_percent", 0) >= 20: score += .18; evidence.append("heart rate increased from personal baseline"); trends.append("heart rate increasing relative to baseline")
        if baseline.get("hrv_delta_percent") is not None and baseline["hrv_delta_percent"] <= -20: score += .15; evidence.append("HRV decreased from personal baseline"); trends.append("HRV decreasing relative to baseline")
        if symptoms: score += min(.15, .04 * len(symptoms)); evidence.append("reported symptoms: " + ", ".join(symptoms[:3]))
        score = round(min(score, .95), 2)
        level = "HIGH" if score >= .7 else "MODERATE" if score >= .35 else "LOW"
        conditions = [{"condition": "possible_abnormal_rhythm", "risk": score}] if level != "LOW" else []
        return AssessmentOutput(risk_level=level, risk_score=score, confidence=.65 if baseline else .45, conditions_of_concern=conditions, evidence=evidence or ["No elevated indicators identified in the available measurement."], trends=trends or ["Longitudinal evidence unavailable or stable."], recommended_action="clinical_evaluation_recommended" if level != "LOW" else "continue_routine_monitoring", specialist="cardiology" if level == "HIGH" else None)


class BaseModelAIService(MockAIService):
    """Safe prototype fallback until a configured OpenAI-compatible model is available."""


class FineTunedLLMService(MockAIService):
    """Runtime placeholder for an offline Unsloth-trained model; never required at startup."""


def get_ai_service(provider: str) -> BaseAIAssessmentService:
    services = {"mock": MockAIService, "base": BaseModelAIService, "finetuned": FineTunedLLMService}
    if provider not in services: raise ValueError("AI_PROVIDER must be mock, base, or finetuned")
    return services[provider]()


def build_prompt(payload: dict) -> str:
    return """You are an early-risk screening assistant, not a diagnostic system. Use only supplied data; do not invent measurements, symptoms, or history. Explain uncertainty, recommend professional evaluation where appropriate, and output only requested JSON.\n\n""" + str(payload)
