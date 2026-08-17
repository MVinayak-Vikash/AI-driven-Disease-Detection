from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ConditionOfConcern(BaseModel):
    condition: str = Field(..., description="Condition key e.g. possible_abnormal_rhythm, metabolic_strain")
    risk: float = Field(..., ge=0.0, le=1.0, description="Risk probability score (0.0 to 1.0)")
    label: Optional[str] = Field(None, description="Human readable label")
    icdCode: Optional[str] = Field(None, description="Relevant ICD-10 reference code")

class AIAssessmentRequest(BaseModel):
    symptoms: Optional[List[str]] = Field(default_factory=list, description="Presenting symptoms e.g. dizziness, fatigue")
    additional_notes: Optional[str] = Field(None, description="Optional clinical observations")

class LLMPatientContext(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: List[str] = Field(default_factory=list)

class LLMSensorContext(BaseModel):
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    hrv: Optional[float] = None
    rhythm_irregularity: Optional[float] = None
    signal_quality: Optional[float] = None

class LLMStructuredInput(BaseModel):
    patient: LLMPatientContext
    symptoms: List[str] = Field(default_factory=list)
    current_sensor: LLMSensorContext
    baseline: Optional[Dict[str, Any]] = None
    trend: Optional[Dict[str, Any]] = None

class AIAssessmentResponse(BaseModel):
    id: Optional[str] = None
    session_id: str
    risk_level: str = Field(..., description="'LOW', 'MODERATE', or 'HIGH'")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Overall risk index (0 to 100)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model certainty/confidence (0.0 to 1.0)")
    conditions_of_concern: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    trends: List[str] = Field(default_factory=list)
    recommended_action: str
    specialist: str
    model_name: Optional[str] = "cardionav-reasoner"
    model_version: Optional[str] = "1.0.0"
    raw_response: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
