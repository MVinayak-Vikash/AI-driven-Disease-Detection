from typing import Dict, Any
from fastapi import APIRouter, Depends
from backend.app.core.config import settings
from backend.app.core.security import get_current_user
from backend.app.schemas.auth import HealthResponse, UserResponse

router = APIRouter(tags=["Authentication & Health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint providing runtime and service metadata."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        ai_provider=settings.AI_PROVIDER,
        database="supabase" if "placeholder" not in settings.SUPABASE_URL else "in-memory-dev"
    )

@router.get("/api/me", response_model=UserResponse)
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns the authenticated Supabase user profile claims."""
    return UserResponse(
        id=user.get("sub", ""),
        email=user.get("email"),
        role=user.get("role", "authenticated"),
        app_metadata=user.get("app_metadata", {}),
        user_metadata=user.get("user_metadata", {})
    )
