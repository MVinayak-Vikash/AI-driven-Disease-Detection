from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class BaselineDelta(BaseModel):
    baseline_hr: Optional[float] = None
    baseline_hrv: Optional[float] = None
    hr_delta: Optional[float] = None
    hr_delta_percent: Optional[float] = None
    hrv_delta: Optional[float] = None
    hrv_delta_percent: Optional[float] = None
    has_baseline: bool = False

class TrendDelta(BaseModel):
    hr_trend_direction: Optional[str] = None # "increasing", "decreasing", "stable"
    hrv_trend_direction: Optional[str] = None
    session_count_evaluated: int = 0
    has_trend: bool = False

class PhysiologicalFeaturesResponse(BaseModel):
    id: str
    session_id: str
    heart_rate_mean: Optional[float] = None
    heart_rate_min: Optional[float] = None
    heart_rate_max: Optional[float] = None
    hrv: Optional[float] = None
    rmssd: Optional[float] = None
    rhythm_irregularity: Optional[float] = None
    signal_quality: Optional[float] = None
    baseline_delta: Optional[Dict[str, Any]] = None
    trend_delta: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
