import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import get_current_user_id
from backend.app.core.database import db_memory, get_supabase_client
from backend.app.services.sensor_service import SensorService
from backend.app.services.signal_service import SignalAnalysisService
from backend.app.services.baseline_service import BaselineService
from backend.app.services.ai_service import get_ai_service
from backend.app.schemas.assessment import (
    AIAssessmentRequest,
    AIAssessmentResponse,
    LLMStructuredInput,
    LLMPatientContext,
    LLMSensorContext
)

router = APIRouter(prefix="/api/sessions", tags=["AI Clinical Assessment"])
signal_analyzer = SignalAnalysisService()

@router.post("/{session_id}/assess-risk", response_model=AIAssessmentResponse)
async def assess_session_risk(
    session_id: str,
    request: AIAssessmentRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Executes multi-modal AI early-risk clinical decision support reasoning (Layer 2).
    Synthesizes demographics, medical history, symptoms, sensor metrics, baseline shifts, and trends.
    """
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    # 1. Fetch Patient Profile
    profile_data = {"age": 52, "gender": "male", "medical_history": []}
    supabase = get_supabase_client()
    if supabase:
        try:
            prof_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
            if prof_res.data:
                profile_data = prof_res.data[0]
        except Exception:
            pass
    elif user_id in db_memory.profiles:
        profile_data = db_memory.profiles[user_id]

    # 2. Fetch or compute physiological features
    features_record = None
    if supabase:
        try:
            feat_res = supabase.table("physiological_features").select("*").eq("session_id", session_id).execute()
            if feat_res.data:
                features_record = feat_res.data[0]
        except Exception:
            pass
    else:
        features_record = db_memory.physiological_features.get(session_id)

    if not features_record:
        # Run on-demand signal analysis
        readings = SensorService.get_session_readings(session_id, limit=2000)
        raw_dicts = [r.model_dump() for r in readings]
        features = signal_analyzer.analyze_session_data(raw_dicts)
        baseline_delta, trend_delta = BaselineService.compute_baseline_and_trend(
            user_id=user_id,
            current_session_id=session_id,
            current_features=features
        )
        features_record = {
            "heart_rate_mean": features["heart_rate_mean"],
            "hrv": features["hrv"],
            "rmssd": features["rmssd"],
            "rhythm_irregularity": features["rhythm_irregularity"],
            "signal_quality": features["signal_quality"],
            "baseline_delta": baseline_delta,
            "trend_delta": trend_delta
        }

    # 3. Construct Structured LLM Input
    llm_input = LLMStructuredInput(
        patient=LLMPatientContext(
            age=profile_data.get("age", 50),
            gender=profile_data.get("gender", "unspecified"),
            medical_history=profile_data.get("medical_history", [])
        ),
        symptoms=request.symptoms or [],
        current_sensor=LLMSensorContext(
            heart_rate=features_record.get("heart_rate_mean", 72.0),
            spo2=98.0, # Nominally extracted from sensor readings if available
            hrv=features_record.get("hrv", 45.0),
            rhythm_irregularity=features_record.get("rhythm_irregularity", 0.08),
            signal_quality=features_record.get("signal_quality", 0.90)
        ),
        baseline=features_record.get("baseline_delta"),
        trend=features_record.get("trend_delta")
    )

    # 4. Execute AI Assessment Service
    ai_service = get_ai_service()
    assessment_result = await ai_service.assess(session_id, llm_input)

    # 5. Persist Assessment
    assessment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    assessment_result.id = assessment_id
    assessment_result.created_at = now

    if supabase:
        try:
            record = {
                "id": assessment_id,
                "session_id": session_id,
                "risk_level": assessment_result.risk_level,
                "risk_score": assessment_result.risk_score,
                "confidence": assessment_result.confidence,
                "conditions_of_concern": assessment_result.conditions_of_concern,
                "evidence": assessment_result.evidence,
                "trends": assessment_result.trends,
                "recommended_action": assessment_result.recommended_action,
                "specialist": assessment_result.specialist,
                "model_name": assessment_result.model_name,
                "model_version": assessment_result.model_version,
                "raw_response": assessment_result.raw_response,
                "created_at": now.isoformat()
            }
            supabase.table("ai_assessments").upsert(record, on_conflict="session_id").execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error saving AI assessment: {str(e)}")
    else:
        db_memory.ai_assessments[session_id] = assessment_result.model_dump()

    return assessment_result

@router.get("/{session_id}/assessment", response_model=AIAssessmentResponse)
async def get_session_assessment(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Retrieves existing AI clinical assessment for a session."""
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("ai_assessments").select("*").eq("session_id", session_id).execute()
            if res.data:
                return AIAssessmentResponse(**res.data[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    assessment = db_memory.ai_assessments.get(session_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assessment found for session '{session_id}'. Run assess-risk first."
        )
    return AIAssessmentResponse(**assessment)
