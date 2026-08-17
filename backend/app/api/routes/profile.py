from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import get_current_user_id
from backend.app.core.database import db_memory, get_supabase_client
from backend.app.schemas.profile import ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/api/profile", tags=["Patient Profile"])

@router.get("", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user_id)):
    """Retrieves the authenticated user's patient profile."""
    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("profiles").select("*").eq("id", user_id).execute()
            if res.data:
                return ProfileResponse(**res.data[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    if user_id in db_memory.profiles:
        return ProfileResponse(**db_memory.profiles[user_id])
    
    # Return default empty profile if none exists yet
    return ProfileResponse(
        id=user_id,
        name=None,
        age=None,
        gender=None,
        medical_history=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """Creates or updates the authenticated user's patient profile."""
    now = datetime.now(timezone.utc)
    update_dict = {
        "id": user_id,
        "name": data.name,
        "age": data.age,
        "gender": data.gender,
        "medical_history": data.medical_history or [],
        "updated_at": now.isoformat()
    }

    supabase = get_supabase_client()
    if supabase:
        try:
            res = supabase.table("profiles").upsert(update_dict).execute()
            if res.data:
                return ProfileResponse(**res.data[0])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error updating profile: {str(e)}")

    profile_obj = {
        "id": user_id,
        "name": data.name,
        "age": data.age,
        "gender": data.gender,
        "medical_history": data.medical_history or [],
        "created_at": db_memory.profiles.get(user_id, {}).get("created_at", now),
        "updated_at": now
    }
    db_memory.profiles[user_id] = profile_obj
    return ProfileResponse(**profile_obj)
