import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

from backend.app.core.database import db_memory, get_supabase_client
from backend.app.schemas.session import SessionCreate, SessionResponse
from backend.app.schemas.sensor import SensorReadingCreate, SensorReadingResponse

class SensorService:
    @staticmethod
    def create_session(user_id: str, data: SessionCreate) -> SessionResponse:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("measurement_sessions").insert({
                    "id": session_id,
                    "user_id": user_id,
                    "device_id": data.device_id,
                    "started_at": now.isoformat(),
                    "status": "active"
                }).execute()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error creating session: {str(e)}")
        else:
            db_memory.measurement_sessions[session_id] = {
                "id": session_id,
                "user_id": user_id,
                "device_id": data.device_id,
                "started_at": now,
                "ended_at": None,
                "status": "active"
            }
            db_memory.sensor_readings[session_id] = []

        return SessionResponse(
            id=session_id,
            user_id=user_id,
            device_id=data.device_id,
            started_at=now,
            status="active"
        )

    @staticmethod
    def get_session(user_id: str, session_id: str) -> Optional[SessionResponse]:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("measurement_sessions").select("*").eq("id", session_id).eq("user_id", user_id).execute()
                if not res.data:
                    return None
                return SessionResponse(**res.data[0])
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        sess = db_memory.measurement_sessions.get(session_id)
        if sess and sess["user_id"] == user_id:
            return SessionResponse(**sess)
        return None

    @staticmethod
    def list_sessions(user_id: str) -> List[SessionResponse]:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("measurement_sessions").select("*").eq("user_id", user_id).order("started_at", desc=True).execute()
                return [SessionResponse(**row) for row in (res.data or [])]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        user_sessions = [
            SessionResponse(**s) for s in db_memory.measurement_sessions.values()
            if s["user_id"] == user_id
        ]
        user_sessions.sort(key=lambda x: x.started_at, reverse=True)
        return user_sessions

    @staticmethod
    def finish_session(user_id: str, session_id: str) -> Optional[SessionResponse]:
        now = datetime.now(timezone.utc)
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("measurement_sessions").update({
                    "ended_at": now.isoformat(),
                    "status": "completed"
                }).eq("id", session_id).eq("user_id", user_id).execute()
                if not res.data:
                    return None
                return SessionResponse(**res.data[0])
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        sess = db_memory.measurement_sessions.get(session_id)
        if sess and sess["user_id"] == user_id:
            sess["ended_at"] = now
            sess["status"] = "completed"
            return SessionResponse(**sess)
        return None

    @staticmethod
    def get_or_create_active_session_for_device(device: Dict[str, Any]) -> str:
        """
        Finds the most recent active session for this device or creates a new one.
        """
        user_id = device["user_id"]
        device_id = device["id"]

        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("measurement_sessions") \
                    .select("id") \
                    .eq("device_id", device_id) \
                    .eq("status", "active") \
                    .order("started_at", desc=True) \
                    .limit(1).execute()
                if res.data:
                    return res.data[0]["id"]
            except Exception:
                pass
        else:
            for s in reversed(list(db_memory.measurement_sessions.values())):
                if s.get("device_id") == device_id and s.get("status") == "active":
                    return s["id"]

        # Create session if none active
        new_sess = SensorService.create_session(user_id, SessionCreate(device_id=device_id))
        return new_sess.id

    @staticmethod
    def ingest_reading(session_id: str, reading: SensorReadingCreate) -> SensorReadingResponse:
        reading_id = str(uuid.uuid4())
        
        # Parse timestamp
        if reading.timestamp is None:
            ts = datetime.now(timezone.utc)
        elif isinstance(reading.timestamp, (int, float)):
            ts = datetime.fromtimestamp(reading.timestamp, tz=timezone.utc)
        else:
            ts = reading.timestamp

        hr = reading.heart_rate
        spo2 = reading.spo2
        sqi = reading.signal_quality
        ppg = reading.ppg

        supabase = get_supabase_client()
        if supabase:
            try:
                supabase.table("sensor_readings").insert({
                    "id": reading_id,
                    "session_id": session_id,
                    "timestamp": ts.isoformat(),
                    "heart_rate": hr,
                    "spo2": spo2,
                    "ppg_data": ppg,
                    "signal_quality": sqi
                }).execute()
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error saving sensor reading: {str(e)}")
        else:
            if session_id not in db_memory.sensor_readings:
                db_memory.sensor_readings[session_id] = []
            db_memory.sensor_readings[session_id].append({
                "id": reading_id,
                "session_id": session_id,
                "timestamp": ts,
                "heart_rate": hr,
                "spo2": spo2,
                "ppg_data": ppg,
                "signal_quality": sqi
            })

        return SensorReadingResponse(
            id=reading_id,
            session_id=session_id,
            timestamp=ts,
            heart_rate=hr,
            spo2=spo2,
            ppg_data=ppg,
            signal_quality=sqi
        )

    @staticmethod
    def get_session_readings(session_id: str, limit: int = 500) -> List[SensorReadingResponse]:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("sensor_readings") \
                    .select("*") \
                    .eq("session_id", session_id) \
                    .order("timestamp", desc=False) \
                    .limit(limit).execute()
                return [SensorReadingResponse(**row) for row in (res.data or [])]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error retrieving readings: {str(e)}")
        
        raw_list = db_memory.sensor_readings.get(session_id, [])
        return [SensorReadingResponse(**r) for r in raw_list[:limit]]
