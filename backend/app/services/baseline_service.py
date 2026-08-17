from typing import Dict, Any, List, Optional, Tuple
from backend.app.core.database import db_memory, get_supabase_client

class BaselineService:
    @staticmethod
    def compute_baseline_and_trend(
        user_id: str,
        current_session_id: str,
        current_features: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Calculates personal baseline averages and longitudinal trend direction
        across the user's historical measurement sessions.
        """
        current_hr = current_features.get("heart_rate_mean") or current_features.get("heart_rate", 72.0)
        current_hrv = current_features.get("hrv") or current_features.get("rmssd", 45.0)

        # Retrieve past physiological features for this user
        historical_features = BaselineService._get_user_historical_features(user_id, current_session_id)

        # If no previous history exists, explicitly return null indicators
        if not historical_features:
            baseline_delta = {
                "has_baseline": False,
                "baseline_hr": None,
                "baseline_hrv": None,
                "hr_delta": None,
                "hr_delta_percent": None,
                "hrv_delta": None,
                "hrv_delta_percent": None
            }
            trend_delta = {
                "has_trend": False,
                "session_count_evaluated": 0,
                "hr_trend_direction": None,
                "hrv_trend_direction": None
            }
            return baseline_delta, trend_delta

        # Calculate historical baseline averages
        past_hrs = [f["heart_rate_mean"] for f in historical_features if f.get("heart_rate_mean") is not None]
        past_hrvs = [f["hrv"] for f in historical_features if f.get("hrv") is not None]

        if not past_hrs or not past_hrvs:
            baseline_delta = {
                "has_baseline": False,
                "baseline_hr": None,
                "baseline_hrv": None,
                "hr_delta": None,
                "hr_delta_percent": None,
                "hrv_delta": None,
                "hrv_delta_percent": None
            }
            trend_delta = {
                "has_trend": False,
                "session_count_evaluated": len(historical_features),
                "hr_trend_direction": None,
                "hrv_trend_direction": None
            }
            return baseline_delta, trend_delta

        baseline_hr = float(sum(past_hrs) / len(past_hrs))
        baseline_hrv = float(sum(past_hrvs) / len(past_hrvs))

        hr_delta = current_hr - baseline_hr
        hr_delta_percent = ((current_hr - baseline_hr) / baseline_hr) * 100.0 if baseline_hr > 0 else 0.0

        hrv_delta = current_hrv - baseline_hrv
        hrv_delta_percent = ((current_hrv - baseline_hrv) / baseline_hrv) * 100.0 if baseline_hrv > 0 else 0.0

        baseline_delta = {
            "has_baseline": True,
            "baseline_hr": round(baseline_hr, 1),
            "baseline_hrv": round(baseline_hrv, 1),
            "hr_delta": round(hr_delta, 1),
            "hr_delta_percent": round(hr_delta_percent, 1),
            "hrv_delta": round(hrv_delta, 1),
            "hrv_delta_percent": round(hrv_delta_percent, 1)
        }

        # Determine trend direction (if >= 2 historical sessions available)
        all_hrs = past_hrs + [current_hr]
        all_hrvs = past_hrvs + [current_hrv]

        hr_direction = "stable"
        if hr_delta_percent > 12.0:
            hr_direction = "increasing"
        elif hr_delta_percent < -12.0:
            hr_direction = "decreasing"

        hrv_direction = "stable"
        if hrv_delta_percent > 15.0:
            hrv_direction = "increasing"
        elif hrv_delta_percent < -15.0:
            hrv_direction = "decreasing"

        trend_delta = {
            "has_trend": len(historical_features) >= 1,
            "session_count_evaluated": len(historical_features) + 1,
            "hr_trend_direction": hr_direction,
            "hrv_trend_direction": hrv_direction
        }

        return baseline_delta, trend_delta

    @staticmethod
    def _get_user_historical_features(user_id: str, exclude_session_id: str) -> List[Dict[str, Any]]:
        """
        Fetches past physiological feature records for a user's completed sessions.
        """
        supabase = get_supabase_client()
        if supabase:
            try:
                # 1. Get session IDs belonging to this user
                sess_res = supabase.table("measurement_sessions") \
                    .select("id") \
                    .eq("user_id", user_id) \
                    .neq("id", exclude_session_id) \
                    .execute()
                session_ids = [s["id"] for s in (sess_res.data or [])]

                if not session_ids:
                    return []

                # 2. Get physiological features for those sessions
                feat_res = supabase.table("physiological_features") \
                    .select("*") \
                    .in_("session_id", session_ids) \
                    .order("created_at", desc=False) \
                    .execute()
                return feat_res.data or []
            except Exception:
                pass

        # Memory store lookup
        user_session_ids = {
            s["id"] for s in db_memory.measurement_sessions.values()
            if s["user_id"] == user_id and s["id"] != exclude_session_id
        }

        features = [
            f for f in db_memory.physiological_features.values()
            if f.get("session_id") in user_session_ids
        ]
        features.sort(key=lambda x: x.get("created_at", 0))
        return features
