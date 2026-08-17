def test_sensor_ingestion_and_validation(client, auth_headers):
    # 1. Create a session
    sess_res = client.post("/api/sessions", json={}, headers=auth_headers)
    session_id = sess_res.json()["id"]

    # 2. Ingest valid reading
    valid_payload = {
        "heart_rate": 82.0,
        "spo2": 97.0,
        "signal_quality": 0.94,
        "ppg": [0.12, 0.14, 0.18, 0.15]
    }
    res = client.post(f"/api/sessions/{session_id}/readings", json=valid_payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["heart_rate"] == 82.0
    assert data["spo2"] == 97.0
    assert len(data["ppg_data"]) == 4

    # 3. Rejection of invalid HR (> 260)
    invalid_hr = {"heart_rate": 450.0}
    res_err1 = client.post(f"/api/sessions/{session_id}/readings", json=invalid_hr, headers=auth_headers)
    assert res_err1.status_code == 422

    # 4. Rejection of invalid SpO2 (> 100)
    invalid_spo2 = {"spo2": 105.0}
    res_err2 = client.post(f"/api/sessions/{session_id}/readings", json=invalid_spo2, headers=auth_headers)
    assert res_err2.status_code == 422

    # 5. Rejection of invalid signal quality (> 1.0)
    invalid_sqi = {"signal_quality": 1.5}
    res_err3 = client.post(f"/api/sessions/{session_id}/readings", json=invalid_sqi, headers=auth_headers)
    assert res_err3.status_code == 422

    # 6. Retrieve stored readings
    get_res = client.get(f"/api/sessions/{session_id}/readings", headers=auth_headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1

def test_hardware_device_sensor_ingestion(client):
    payload = {
        "device_id": "ESP32-A8F31",
        "heart_rate": 84.0,
        "spo2": 98.0,
        "signal_quality": 0.95,
        "ppg": [0.2, 0.4, 0.6, 0.3]
    }
    res = client.post("/api/devices/ESP32-A8F31/readings", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ingested"
    assert "session_id" in res.json()
