def test_session_lifecycle_and_ownership(client, auth_headers, other_auth_headers):
    # 1. Create measurement session
    res = client.post("/api/sessions", json={}, headers=auth_headers)
    assert res.status_code == 201
    session_id = res.json()["id"]
    assert res.json()["status"] == "active"

    # 2. List sessions for User A
    list_res = client.get("/api/sessions", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 3. User B cannot access User A's session
    other_get = client.get(f"/api/sessions/{session_id}", headers=other_auth_headers)
    assert other_get.status_code == 404

    # 4. User A can finish session
    finish_res = client.post(f"/api/sessions/{session_id}/finish", headers=auth_headers)
    assert finish_res.status_code == 200
    assert finish_res.json()["status"] == "completed"
    assert finish_res.json()["ended_at"] is not None
