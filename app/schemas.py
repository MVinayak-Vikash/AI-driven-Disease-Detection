from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileUpdate(APIModel):
    name: str | None = Field(None, max_length=200)
    date_of_birth: date | None = None
    age: int | None = Field(None, ge=0, le=130)
    gender: str | None = Field(None, max_length=60)
    medical_history: list[str] = Field(default_factory=list, max_length=50)


class DeviceCreate(APIModel):
    device_uid: str = Field(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_.-]+$")
    device_name: str | None = Field(None, max_length=100)
    device_type: str = Field(default="ESP32_MAX30102", max_length=100)


class SessionCreate(APIModel):
    device_id: UUID


class ReadingCreate(APIModel):
    device_id: str | None = Field(None, max_length=100)
    session_id: UUID | None = None
    timestamp: datetime | int | float | None = None
    heart_rate: float | None = Field(None, ge=20, le=250)
    spo2: float | None = Field(None, ge=50, le=100)
    signal_quality: float | None = Field(None, ge=0, le=1)
    ppg: list[float] | None = Field(None, max_length=2048)

    @field_validator("ppg")
    @classmethod
    def finite_ppg(cls, value):
        if value is not None and any(not (-1_000_000 < sample < 1_000_000) for sample in value):
            raise ValueError("PPG values are outside accepted range")
        return value

    def has_measurement(self) -> bool:
        return any(value is not None for value in (self.heart_rate, self.spo2, self.signal_quality, self.ppg))


class AssessmentRequest(APIModel):
    symptoms: list[str] = Field(default_factory=list, max_length=30)


class ConditionOfConcern(APIModel):
    condition: str = Field(max_length=100)
    risk: float = Field(ge=0, le=1)


class AssessmentOutput(APIModel):
    risk_level: Literal["LOW", "MODERATE", "HIGH"]
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    conditions_of_concern: list[ConditionOfConcern]
    evidence: list[str]
    trends: list[str]
    recommended_action: str
    specialist: str | None = None
