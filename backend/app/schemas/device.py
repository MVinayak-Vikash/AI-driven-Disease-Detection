from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class DeviceCreate(BaseModel):
    device_uid: str = Field(..., description="Unique hardware identifier (e.g. ESP32-A8F31)")
    device_name: str = Field(..., description="Human-friendly name for device")
    device_type: Optional[str] = Field("ESP32_MAX30102", description="Sensor board type")
    device_token: Optional[str] = Field(None, description="Secret token for device authentication; if omitted, backend generates one")

class DeviceResponse(BaseModel):
    id: str
    user_id: str
    device_uid: str
    device_name: str
    device_type: str
    status: str
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    generated_token: Optional[str] = Field(None, description="Returned only during device creation for hardware flashing")

    model_config = ConfigDict(from_attributes=True)
