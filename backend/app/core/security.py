import hashlib
import hmac
import jwt
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.app.core.config import settings

security = HTTPBearer(auto_error=False)

def hash_device_token(token: str) -> str:
    """Generate SHA-256 hash for device credentials."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

def verify_device_token(raw_token: str, stored_hash: str) -> bool:
    """Constant-time verification of device token hash."""
    computed_hash = hash_device_token(raw_token)
    return hmac.compare_digest(computed_hash, stored_hash)

def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a Supabase JWT token.
    Extracts the user's UUID claim (`sub`).
    """
    try:
        # If a JWT secret is configured, verify signature
        if settings.SUPABASE_JWT_SECRET and settings.SUPABASE_JWT_SECRET != "your-supabase-jwt-secret-here":
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_aud": False}
            )
        else:
            # Fallback to unverified decode for development/testing when secret is unset
            payload = jwt.decode(token, options={"verify_signature": False})
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject (user ID) claim"
            )
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )

async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and verify the authenticated Supabase user.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer header"
        )
    return decode_supabase_jwt(auth.credentials)

async def get_current_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """
    FastAPI dependency returning the canonical UUID string of the authenticated user.
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user ID not found in token"
        )
    return str(user_id)
