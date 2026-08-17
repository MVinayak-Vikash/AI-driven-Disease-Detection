import numpy as np
from backend.app.services.signal_service import SignalAnalysisService

def test_signal_analysis_deterministic_calculations():
    service = SignalAnalysisService()

    # Synthetic readings with fluctuating heart rates
    readings = [
        {"heart_rate": 70.0, "spo2": 98.0, "signal_quality": 0.95, "ppg_data": None},
        {"heart_rate": 74.0, "spo2": 98.0, "signal_quality": 0.94, "ppg_data": None},
        {"heart_rate": 78.0, "spo2": 97.0, "signal_quality": 0.93, "ppg_data": None},
        {"heart_rate": 72.0, "spo2": 99.0, "signal_quality": 0.96, "ppg_data": None},
    ]

    features = service.analyze_session_data(readings)
    assert features["heart_rate_mean"] == 73.5
    assert features["heart_rate_min"] == 70.0
    assert features["heart_rate_max"] == 78.0
    assert features["hrv"] > 0
    assert features["rmssd"] > 0
    assert 0.0 <= features["rhythm_irregularity"] <= 1.0
    assert 0.0 <= features["signal_quality"] <= 1.0

def test_signal_analysis_waveform_peak_detection():
    service = SignalAnalysisService()

    # Generate 5 seconds of synthetic PPG pulses at 1.2 Hz (72 BPM) at 50 Hz sampling rate
    fs = 50.0
    t = np.linspace(0, 5, int(fs * 5))
    waveform = np.sin(2 * np.pi * 1.2 * t) + 0.3 * np.sin(2 * np.pi * 2.4 * t)
    
    readings = [
        {"heart_rate": None, "spo2": 98.0, "signal_quality": 0.95, "ppg_data": waveform.tolist()}
    ]

    features = service.analyze_session_data(readings, sampling_rate_hz=fs)
    assert 60.0 <= features["heart_rate_mean"] <= 85.0
    assert features["hrv"] > 0
    assert features["rmssd"] > 0
    assert features["signal_quality"] > 0.6
