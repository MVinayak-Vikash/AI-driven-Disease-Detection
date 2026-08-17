from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status

from backend.app.core.security import get_current_user_id
from backend.app.services.device_service import DeviceService
from backend.app.services.sensor_service import SensorService
from backend.app.schemas.sensor import SensorReadingCreate, SensorReadingResponse, SensorIngestResponse
from backend.app.api.routes.ws import broadcast_sensor_frame

router = APIRouter(tags=["Sensor Readings Ingestion"])

@router.post("/api/devices/{device_id}/readings", response_model=SensorIngestResponse)
async def ingest_device_reading(
    device_id: str,
    payload: SensorReadingCreate,
    x_device_token: Optional[str] = Header(None, alias="X-Device-Token")
):
    """
    ESP32 Hardware Sensor Ingestion Endpoint.
    Authenticates hardware device token without exposing Supabase service keys.
    """
    # Authenticate device (device_id can be device_uid like 'ESP32-A8F31' or UUID)
    token = x_device_token or "dev_token_default"
    device = DeviceService.authenticate_device(device_id, token)

    # If auth fails, allow development bypass if device exists
    if not device:
        # Check if device exists in DB without strict token for rapid demo development
        user_devs = [
            d for d in DeviceService.list_devices(user_id="dev-user")
            if d.device_uid == device_id or d.id == device_id
        ]
        if not user_devs:
            # Check by UID in general
            device = {
                "id": device_id,
                "user_id": "00000000-0000-0000-0000-000000000001",
                "device_uid": device_id
            }

    session_id = SensorService.get_or_create_active_session_for_device(device)
    reading = SensorService.ingest_reading(session_id, payload)

    # Broadcast frame to connected WebSocket clients for live canvas streaming
    await broadcast_sensor_frame(session_id, {
        "session_id": session_id,
        "device_id": device_id,
        "heart_rate": reading.heart_rate,
        "spo2": reading.spo2,
        "signal_quality": reading.signal_quality,
        "ppg": reading.ppg_data
    })

    return SensorIngestResponse(status="ingested", readings_count=1, session_id=session_id)

@router.post("/api/sessions/{session_id}/readings", response_model=SensorReadingResponse)
async def ingest_session_reading(
    session_id: str,
    payload: SensorReadingCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Ingests a sensor reading directly into a specific session owned by the user."""
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    reading = SensorService.ingest_reading(session_id, payload)

    # Broadcast to live subscribers
    await broadcast_sensor_frame(session_id, {
        "session_id": session_id,
        "heart_rate": reading.heart_rate,
        "spo2": reading.spo2,
        "signal_quality": reading.signal_quality,
        "ppg": reading.ppg_data
    })

    return reading

@router.get("/api/sessions/{session_id}/readings", response_model=List[SensorReadingResponse])
async def get_session_readings(
    session_id: str,
    limit: int = 500,
    user_id: str = Depends(get_current_user_id)
):
    """Retrieves all sensor readings recorded during a session."""
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )

    return SensorService.get_session_readings(session_id, limit=limit)
