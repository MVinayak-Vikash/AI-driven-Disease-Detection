import pytest
from fastapi import HTTPException
from app.auth import get_current_user
from app.config import get_settings
from app.main import health
from app.schemas import ReadingCreate


@pytest.mark.asyncio
async def test_health():
    assert await health() == {"status": "ok"}


@pytest.mark.asyncio
async def test_protected_route_rejects_missing_token():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None, get_settings())
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_malformed_sensor_payload_rejected_before_auth():
    # Pydantic limits physiological values even when valid authorization is supplied later.
    with pytest.raises(ValueError):
        ReadingCreate(heart_rate=999)
