from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import get_current_user_id
from backend.app.services.sensor_service import SensorService
from backend.app.schemas.session import SessionCreate, SessionResponse

router = APIRouter(prefix="/api/sessions", tags=["Measurement Sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Creates a new measurement recording session linked to the user."""
    return SensorService.create_session(user_id, data)

@router.get("", response_model=List[SessionResponse])
async def list_sessions(user_id: str = Depends(get_current_user_id)):
    """Lists all measurement sessions belonging to the user."""
    return SensorService.list_sessions(user_id)

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Retrieves session metadata by ID."""
    session = SensorService.get_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )
    return session

@router.post("/{session_id}/finish", response_model=SessionResponse)
async def finish_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Marks a measurement recording session as completed."""
    session = SensorService.finish_session(user_id, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found or access denied."
        )
    return session
