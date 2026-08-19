from dataclasses import dataclass
from fastapi import Depends, Header
from .config import Settings, get_settings
from .errors import api_error
from .repository import SupabaseRepository


@dataclass
class CurrentUser:
    id: str
    token: str
    email: str | None = None


async def get_current_user(authorization: str | None = Header(None), settings: Settings = Depends(get_settings)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise api_error(401, "UNAUTHORIZED", "A Supabase access token is required.")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise api_error(401, "UNAUTHORIZED", "A Supabase access token is required.")
    # Supabase Auth verifies signature and issuer at its user endpoint; do not decode unverified JWTs.
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise api_error(503, "AUTH_UNAVAILABLE", "Supabase authentication is not configured.")
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/user", headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        raise api_error(401, "INVALID_TOKEN", "The Supabase access token is invalid or expired.")
    data = response.json()
    return CurrentUser(id=data["id"], token=token, email=data.get("email"))


async def get_repository(user: CurrentUser = Depends(get_current_user), settings: Settings = Depends(get_settings)) -> SupabaseRepository:
    return SupabaseRepository(settings, user.token)
