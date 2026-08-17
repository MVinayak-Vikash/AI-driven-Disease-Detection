import pytest
import jwt
from starlette.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import db_memory

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_OTHER_USER_ID = "00000000-0000-0000-0000-000000000002"
JWT_SECRET_32_BYTES = "super-secret-cardionav-jwt-key-32bytes!!"

def generate_test_jwt(user_id: str = TEST_USER_ID, email: str = "patient@cardionav.ai") -> str:
    """Generates a test Supabase-format JWT."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated"
    }
    return jwt.encode(payload, JWT_SECRET_32_BYTES, algorithm="HS256")

@pytest.fixture(autouse=True)
def clean_db():
    """Clears in-memory DB before each test."""
    db_memory.clear()
    yield
    db_memory.clear()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    token = generate_test_jwt(TEST_USER_ID)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def other_auth_headers():
    token = generate_test_jwt(TEST_OTHER_USER_ID)
    return {"Authorization": f"Bearer {token}"}
