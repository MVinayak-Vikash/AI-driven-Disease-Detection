from backend.app.services.baseline_service import BaselineService
from backend.app.core.database import db_memory

def test_baseline_and_trend_calculation():
    user_id = "00000000-0000-0000-0000-000000000001"
    session_1 = "sess-01"
    session_2 = "sess-02"

    # Case 1: First session (no prior history)
    current_features_1 = {"heart_rate_mean": 74.0, "hrv": 46.0}
    b_delta1, t_delta1 = BaselineService.compute_baseline_and_trend(user_id, session_1, current_features_1)

    assert b_delta1["has_baseline"] is False
    assert b_delta1["baseline_hr"] is None
    assert t_delta1["has_trend"] is False

    # Simulate completed Session 1 saved to database
    db_memory.measurement_sessions[session_1] = {
        "id": session_1,
        "user_id": user_id,
        "status": "completed"
    }
    db_memory.physiological_features[session_1] = {
        "id": "feat-01",
        "session_id": session_1,
        "heart_rate_mean": 74.0,
        "hrv": 46.0
    }

    # Case 2: Second session (evaluated against Session 1 baseline)
    current_features_2 = {"heart_rate_mean": 94.0, "hrv": 29.0}
    b_delta2, t_delta2 = BaselineService.compute_baseline_and_trend(user_id, session_2, current_features_2)

    assert b_delta2["has_baseline"] is True
    assert b_delta2["baseline_hr"] == 74.0
    assert b_delta2["baseline_hrv"] == 46.0
    assert b_delta2["hr_delta"] == 20.0 # 94 - 74
    assert b_delta2["hr_delta_percent"] > 25.0
    assert b_delta2["hrv_delta"] == -17.0 # 29 - 46
    assert b_delta2["hrv_delta_percent"] < -30.0
    assert t_delta2["hr_trend_direction"] == "increasing"
    assert t_delta2["hrv_trend_direction"] == "decreasing"
