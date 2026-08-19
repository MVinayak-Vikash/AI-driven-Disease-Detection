import pytest
from app.services import SignalAnalysisService, get_ai_service


def test_baseline_and_trend_calculation():
    result = SignalAnalysisService().analyze(
        [{"heart_rate": 90, "signal_quality": .9}, {"heart_rate": 94, "signal_quality": .95}],
        [{"heart_rate_mean": 74, "hrv": 40}, {"heart_rate_mean": 78, "hrv": 35}],
    )
    assert result["baseline_delta"]["heart_rate_delta_percent"] > 15
    assert result["trend_delta"] is not None


def test_no_history_has_no_baseline_or_trend():
    result = SignalAnalysisService().analyze([{"heart_rate": 80}], [])
    assert result["baseline_delta"] is None
    assert result["trend_delta"] is None


@pytest.mark.asyncio
async def test_mock_ai_returns_valid_screening_assessment():
    assessment = await get_ai_service("mock").assess({"current_sensor": {"heart_rate": 108, "rhythm_irregularity": .3}, "baseline": {"heart_rate_delta_percent": 30, "hrv_delta_percent": -30}, "symptoms": ["dizziness"]})
    assert assessment.risk_level in {"LOW", "MODERATE", "HIGH"}
    assert assessment.risk_score <= 1
    assert "diagnos" not in assessment.recommended_action


@pytest.mark.parametrize("provider", ["mock", "base", "finetuned"])
def test_provider_switching(provider):
    assert get_ai_service(provider)


def test_invalid_provider_rejected():
    with pytest.raises(ValueError): get_ai_service("unknown")
