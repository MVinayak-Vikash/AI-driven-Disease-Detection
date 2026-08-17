from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import get_current_user_id
from backend.app.core.database import db_memory, get_supabase_client
from backend.app.services.sensor_service import SensorService

router = APIRouter(prefix="/api/history", tags=["Screening History & Baselines"])

@router.get("", response_model=List[Dict[str, Any]])
async def get_screening_history(user_id: str = Depends(get_current_user_id)):
    """
    Retrieves longitudinal history of all screening sessions, 
    including physiological metrics and AI risk assessments.
    """
    sessions = SensorService.list_sessions(user_id)
    history_records = []

    supabase = get_supabase_client()
    for s in sessions:
        assessment = None
        features = None
        if supabase:
            try:
                a_res = supabase.table("ai_assessments").select("*").eq("session_id", s.id).execute()
                if a_res.data:
                    assessment = a_res.data[0]
                f_res = supabase.table("physiological_features").select("*").eq("session_id", s.id).execute()
                if f_res.data:
                    features = f_res.data[0]
            except Exception:
                pass
        else:
            assessment = db_memory.ai_assessments.get(s.id)
            features = db_memory.physiological_features.get(s.id)

        history_records.append({
            "session_id": s.id,
            "device_id": s.device_id,
            "started_at": s.started_at,
            "ended_at": s.ended_at,
            "status": s.status,
            "features": features,
            "assessment": assessment
        })

    return history_records

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_history_detail(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Retrieves detailed clinical profile and telemetry summary for a single past screening session.
    """
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    supabase = get_supabase_client()
    assessment = None
    features = None
    readings_count = 0

    if supabase:
        try:
            a_res = supabase.table("ai_assessments").select("*").eq("session_id", session_id).execute()
            if a_res.data:
                assessment = a_res.data[0]
            f_res = supabase.table("physiological_features").select("*").eq("session_id", session_id).execute()
            if f_res.data:
                features = f_res.data[0]
            r_res = supabase.table("sensor_readings").select("id", count="exact").eq("session_id", session_id).execute()
            readings_count = r_res.count or len(r_res.data or [])
        except Exception:
            pass
    else:
        assessment = db_memory.ai_assessments.get(session_id)
        features = db_memory.physiological_features.get(session_id)
        readings_count = len(db_memory.sensor_readings.get(session_id, []))

    return {
        "session": session.model_dump(),
        "readings_count": readings_count,
        "features": features,
        "assessment": assessment
    }
