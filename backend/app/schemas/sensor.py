from typing import Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class SensorReadingCreate(BaseModel):
    device_id: Optional[str] = Field(None, description="Device UID or UUID")
    timestamp: Optional[Union[float, int, datetime]] = Field(None, description="Unix timestamp or ISO datetime")
    heart_rate: Optional[float] = Field(None, ge=20.0, le=260.0, description="Heart rate in BPM")
    spo2: Optional[float] = Field(None, ge=40.0, le=100.0, description="Blood oxygen saturation percentage")
    signal_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Perfusion/Signal Quality Index (0-1)")
    ppg: Optional[List[float]] = Field(None, description="Raw PPG array samples")

    # Backwards compatibility / alias support
    bpm: Optional[float] = Field(None, ge=20.0, le=260.0)
    signal: Optional[List[float]] = None
    sqi: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("heart_rate", mode="before")
    @classmethod
    def resolve_heart_rate(cls, v, info):
        if v is not None:
            return v
        data = info.data if hasattr(info, "data") else {}
        return data.get("bpm")

    @field_validator("signal_quality", mode="before")
    @classmethod
    def resolve_signal_quality(cls, v, info):
        if v is not None:
            return v
        data = info.data if hasattr(info, "data") else {}
        return data.get("sqi")

    @field_validator("ppg", mode="before")
    @classmethod
    def resolve_ppg(cls, v, info):
        if v is not None:
            return v
        data = info.data if hasattr(info, "data") else {}
        return data.get("signal")

class SensorReadingResponse(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    ppg_data: Optional[List[float]] = None
    signal_quality: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class SensorIngestResponse(BaseModel):
    status: str = "ingested"
    readings_count: int = 1
    session_id: Optional[str] = None
