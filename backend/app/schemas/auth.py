from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    role: Optional[str] = "authenticated"
    app_metadata: Optional[Dict[str, Any]] = None
    user_metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    ai_provider: str
    database: str
