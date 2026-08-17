def test_device_lifecycle_and_ownership(client, auth_headers, other_auth_headers):
    # 1. Register device for User A
    payload = {
        "device_uid": "ESP32-A8F31",
        "device_name": "Clinic Bedside Sensor",
        "device_type": "ESP32_MAX30102"
    }
    res = client.post("/api/devices", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    device_id = data["id"]
    assert data["device_uid"] == "ESP32-A8F31"
    assert data["generated_token"] is not None

    # 2. List devices for User A
    list_res = client.get("/api/devices", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 3. User B should NOT see User A's device
    other_list = client.get("/api/devices", headers=other_auth_headers)
    assert other_list.status_code == 200
    assert len(other_list.json()) == 0

    # 4. User B cannot access User A's device by ID
    other_get = client.get(f"/api/devices/{device_id}", headers=other_auth_headers)
    assert other_get.status_code == 404

    # 5. User B cannot delete User A's device
    other_del = client.delete(f"/api/devices/{device_id}", headers=other_auth_headers)
    assert other_del.status_code == 404

    # 6. User A can delete own device
    del_res = client.delete(f"/api/devices/{device_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Verify device deleted
    get_after = client.get(f"/api/devices/{device_id}", headers=auth_headers)
    assert get_after.status_code == 404
