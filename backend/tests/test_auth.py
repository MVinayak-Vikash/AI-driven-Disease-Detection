from backend.tests.conftest import TEST_USER_ID

def test_api_me_authenticated(client, auth_headers):
    res = client.get("/api/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == TEST_USER_ID
    assert data["email"] == "patient@cardionav.ai"

def test_api_me_unauthorized(client):
    res = client.get("/api/me")
    assert res.status_code == 401

def test_profile_get_and_update(client, auth_headers):
    # Initial get (default profile)
    res = client.get("/api/profile", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == TEST_USER_ID

    # Update profile
    update_payload = {
        "name": "Vikram Sundaram",
        "age": 54,
        "gender": "male",
        "medical_history": ["hypertension", "smoking"]
    }
    res_update = client.put("/api/profile", json=update_payload, headers=auth_headers)
    assert res_update.status_code == 200
    updated_data = res_update.json()
    assert updated_data["name"] == "Vikram Sundaram"
    assert updated_data["age"] == 54
    assert updated_data["medical_history"] == ["hypertension", "smoking"]

    # Verify persistent retrieval
    res_get = client.get("/api/profile", headers=auth_headers)
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Vikram Sundaram"
