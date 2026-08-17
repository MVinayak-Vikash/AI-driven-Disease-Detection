import pytest
from backend.app.services.ai_service import MockAIService, get_ai_service
from backend.app.schemas.assessment import LLMStructuredInput, LLMPatientContext, LLMSensorContext

@pytest.mark.asyncio
async def test_mock_ai_elevated_risk_assessment():
    mock_service = MockAIService()

    input_data = LLMStructuredInput(
        patient=LLMPatientContext(
            age=52,
            gender="male",
            medical_history=["hypertension"]
        ),
        symptoms=["dizziness", "fatigue", "palpitations"],
        current_sensor=LLMSensorContext(
            heart_rate=108.0,
            spo2=97.0,
            hrv=21.0,
            rhythm_irregularity=0.73,
            signal_quality=0.91
        ),
        baseline={
            "has_baseline": True,
            "baseline_hr": 76.0,
            "baseline_hrv": 44.0,
            "hr_delta_percent": 42.1,
            "hrv_delta_percent": -52.2
        },
        trend={
            "has_trend": True,
            "hr_trend_direction": "increasing",
            "hrv_trend_direction": "decreasing"
        }
    )

    assessment = await mock_service.assess("test-session-123", input_data)
    assert assessment.risk_level == "HIGH"
    assert assessment.risk_score >= 65.0
    assert assessment.confidence >= 0.70
    assert len(assessment.conditions_of_concern) >= 1
    assert len(assessment.evidence) >= 2
    assert len(assessment.trends) >= 1
    assert "Cardiology" in assessment.specialist
    assert assessment.model_name == "mock-cardionav-reasoner"

@pytest.mark.asyncio
async def test_mock_ai_normal_risk_assessment():
    mock_service = MockAIService()

    input_data = LLMStructuredInput(
        patient=LLMPatientContext(age=28, gender="female", medical_history=[]),
        symptoms=[],
        current_sensor=LLMSensorContext(
            heart_rate=72.0,
            spo2=99.0,
            hrv=55.0,
            rhythm_irregularity=0.06,
            signal_quality=0.97
        ),
        baseline={"has_baseline": True, "baseline_hr": 70.0, "baseline_hrv": 54.0, "hr_delta_percent": 2.8, "hrv_delta_percent": 1.8},
        trend={"has_trend": True, "hr_trend_direction": "stable", "hrv_trend_direction": "stable"}
    )

    assessment = await mock_service.assess("test-normal-123", input_data)
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score < 30.0
    assert "Primary Care" in assessment.specialist or "Wellness" in assessment.specialist

def test_ai_provider_factory_switching():
    mock_svc = get_ai_service("mock")
    assert mock_svc.__class__.__name__ == "MockAIService"

    base_svc = get_ai_service("base")
    assert base_svc.__class__.__name__ == "BaseModelAIService"

    fine_svc = get_ai_service("finetuned")
    assert fine_svc.__class__.__name__ == "FineTunedLLMService"

def test_end_to_end_assessment_flow(client, auth_headers):
    # 1. Create Session
    sess_res = client.post("/api/sessions", json={}, headers=auth_headers)
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 2. Ingest sensor reading
    reading_payload = {
        "heart_rate": 108.0,
        "spo2": 96.0,
        "signal_quality": 0.93,
        "ppg": [0.12, 0.45, 0.78, 0.32]
    }
    client.post(f"/api/sessions/{session_id}/readings", json=reading_payload, headers=auth_headers)

    # 3. Analyze Signal
    sig_res = client.post(f"/api/sessions/{session_id}/analyze-signal", headers=auth_headers)
    assert sig_res.status_code == 200
    features = sig_res.json()
    assert features["heart_rate_mean"] == 108.0

    # 4. Assess Risk
    assess_res = client.post(f"/api/sessions/{session_id}/assess-risk", json={"symptoms": ["dizziness", "palpitations"]}, headers=auth_headers)
    assert assess_res.status_code == 200
    assessment = assess_res.json()
    assert "risk_level" in assessment
    assert "conditions_of_concern" in assessment
    assert "recommended_action" in assessment

    # 5. Retrieve Assessment
    get_assess = client.get(f"/api/sessions/{session_id}/assessment", headers=auth_headers)
    assert get_assess.status_code == 200
    assert get_assess.json()["session_id"] == session_id

    # 6. Check History
    hist_res = client.get("/api/history", headers=auth_headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1
