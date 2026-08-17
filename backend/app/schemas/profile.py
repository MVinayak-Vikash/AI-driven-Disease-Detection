from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ProfileBase(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the patient")
    age: Optional[int] = Field(None, ge=0, le=125, description="Patient age in years")
    gender: Optional[str] = Field(None, description="Biological sex / gender")
    medical_history: Optional[List[str]] = Field(default_factory=list, description="List of past diagnoses/risk factors")

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileResponse(ProfileBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
