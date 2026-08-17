from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import get_current_user_id
from backend.app.services.device_service import DeviceService
from backend.app.schemas.device import DeviceCreate, DeviceResponse

router = APIRouter(prefix="/api/devices", tags=["ESP32 Devices"])

@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    data: DeviceCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Registers a new ESP32 device for the authenticated user."""
    return DeviceService.register_device(user_id, data)

@router.get("", response_model=List[DeviceResponse])
async def list_devices(user_id: str = Depends(get_current_user_id)):
    """Lists all ESP32 devices owned by the authenticated user."""
    return DeviceService.list_devices(user_id)

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Retrieves details of a specific device owned by the user."""
    device = DeviceService.get_device(user_id, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found or access denied."
        )
    return device

@router.delete("/{device_id}", status_code=status.HTTP_200_OK)
async def delete_device(
    device_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Deletes/unregisters a device owned by the user."""
    success = DeviceService.delete_device(user_id, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found or access denied."
        )
    return {"status": "deleted", "device_id": device_id}
