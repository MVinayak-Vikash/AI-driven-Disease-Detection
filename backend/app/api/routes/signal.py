import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import get_current_user_id
from backend.app.core.database import db_memory, get_supabase_client
from backend.app.services.sensor_service import SensorService
from backend.app.services.signal_service import SignalAnalysisService
from backend.app.services.baseline_service import BaselineService
from backend.app.schemas.signal import PhysiologicalFeaturesResponse

router = APIRouter(prefix="/api/sessions", tags=["Signal Analysis & Features"])
signal_analyzer = SignalAnalysisService()

@router.post("/{session_id}/analyze-signal", response_model=PhysiologicalFeaturesResponse)
async def analyze_session_signal(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Executes physiological signal processing on session sensor data.
    Extracts HR, HRV/RMSSD, rhythm irregularity, SQI, and personal baseline deltas.
    """
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    readings = SensorService.get_session_readings(session_id, limit=2000)
    raw_dicts = [r.model_dump() for r in readings]

    # Layer 1 Signal Processing
    features = signal_analyzer.analyze_session_data(raw_dicts)

    # Personal baseline and trend computation
    baseline_delta, trend_delta = BaselineService.compute_baseline_and_trend(
        user_id=user_id,
        current_session_id=session_id,
        current_features=features
    )

    feature_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    supabase = get_supabase_client()
    if supabase:
        try:
            record = {
                "id": feature_id,
                "session_id": session_id,
                "heart_rate_mean": features["heart_rate_mean"],
                "heart_rate_min": features["heart_rate_min"],
                "heart_rate_max": features["heart_rate_max"],
                "hrv": features["hrv"],
                "rmssd": features["rmssd"],
                "rhythm_irregularity": features["rhythm_irregularity"],
                "signal_quality": features["signal_quality"],
                "baseline_delta": baseline_delta,
                "trend_delta": trend_delta,
                "created_at": now.isoformat()
            }
            supabase.table("physiological_features").upsert(record, on_conflict="session_id").execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error saving features: {str(e)}")
    else:
        db_memory.physiological_features[session_id] = {
            "id": feature_id,
            "session_id": session_id,
            "heart_rate_mean": features["heart_rate_mean"],
            "heart_rate_min": features["heart_rate_min"],
            "heart_rate_max": features["heart_rate_max"],
            "hrv": features["hrv"],
            "rmssd": features["rmssd"],
            "rhythm_irregularity": features["rhythm_irregularity"],
            "signal_quality": features["signal_quality"],
            "baseline_delta": baseline_delta,
            "trend_delta": trend_delta,
            "created_at": now
        }

    return PhysiologicalFeaturesResponse(
        id=feature_id,
        session_id=session_id,
        heart_rate_mean=features["heart_rate_mean"],
        heart_rate_min=features["heart_rate_min"],
        heart_rate_max=features["heart_rate_max"],
        hrv=features["hrv"],
        rmssd=features["rmssd"],
        rhythm_irregularity=features["rhythm_irregularity"],
        signal_quality=features["signal_quality"],
        baseline_delta=baseline_delta,
        trend_delta=trend_delta,
        created_at=now
    )

@router.get("/{session_id}/features", response_model=PhysiologicalFeaturesResponse)
async def get_session_features(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Retrieves computed physiological features for a session."""
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("physiological_features").select("*").eq("session_id", session_id).execute()
            if res.data:
                return PhysiologicalFeaturesResponse(**res.data[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    feat = db_memory.physiological_features.get(session_id)
    if not feat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Features not yet calculated for session '{session_id}'. Run analyze-signal first."
        )
    return PhysiologicalFeaturesResponse(**feat)
