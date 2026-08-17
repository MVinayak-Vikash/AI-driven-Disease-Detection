from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class SessionCreate(BaseModel):
    device_id: Optional[str] = Field(None, description="UUID of the linked ESP32 device")

class SessionResponse(BaseModel):
    id: str
    user_id: str
    device_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str

    model_config = ConfigDict(from_attributes=True)
