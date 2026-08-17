/**
 * CardioNav AI - REST & WebSocket API Client
 * Seamless integration with FastAPI / Node.js Backend & ESP32 Hardware
 */

import { AIClinicalReasoner } from './ai-reasoner.js';

export class APIClient {
  constructor(options = {}) {
    this.httpBaseUrl = options.httpBaseUrl || 'http://localhost:8000';
    this.wsUrl = options.wsUrl || 'ws://localhost:8000/ws/sensor';
    this.isBackendOnline = false;
    this.wsSocket = null;
    this.wsConnected = false;
    this.localReasoner = new AIClinicalReasoner();

    this.onSensorDataReceived = options.onSensorDataReceived || null;
    this.onConnectionStatusChanged = options.onConnectionStatusChanged || null;
    this.telemetryLogs = [];

    this.checkHealth();
  }

  setEndpoints(httpUrl, wsUrl) {
    this.httpBaseUrl = httpUrl.replace(/\/$/, '');
    this.wsUrl = wsUrl;
    this.checkHealth();
  }

  logTelemetry(type, endpoint, payload, response) {
    const entry = {
      timestamp: new Date().toLocaleTimeString(),
      type,
      endpoint,
      payload,
      response
    };
    this.telemetryLogs.unshift(entry);
    if (this.telemetryLogs.length > 30) this.telemetryLogs.pop();
  }

  async checkHealth() {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1500);
      const res = await fetch(`${this.httpBaseUrl}/health`, { signal: controller.signal });
      clearTimeout(timeoutId);
      this.isBackendOnline = res.ok;
    } catch (e) {
      this.isBackendOnline = false;
    }

    if (this.onConnectionStatusChanged) {
      this.onConnectionStatusChanged({
        backendOnline: this.isBackendOnline,
        wsConnected: this.wsConnected,
        httpUrl: this.httpBaseUrl
      });
    }
    return this.isBackendOnline;
  }

  /**
   * Submits patient context + sensor features for LLM AI Risk Assessment
   */
  async runAssessment(patientData, sensorFeatures) {
    const payload = {
      patient: {
        age: Number(patientData.age),
        sex: patientData.sex,
        name: patientData.fullName,
        bp_systolic: patientData.systolicBp,
        bp_diastolic: patientData.diastolicBp,
        bmi: patientData.bmi
      },
      symptoms: patientData.symptoms,
      history: patientData.history,
      sensor: {
        heart_rate: sensorFeatures.heartRate,
        hrv: sensorFeatures.hrv,
        rhythm_irregularity: sensorFeatures.rhythmIrregularity,
        signal_quality: sensorFeatures.signalQuality,
        spo2: sensorFeatures.spo2
      }
    };

    // If backend is active, try remote endpoint
    if (this.isBackendOnline) {
      try {
        const res = await fetch(`${this.httpBaseUrl}/api/assess`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (res.ok) {
          const data = await res.json();
          this.logTelemetry('REST POST', '/api/assess', payload, data);
          return { data, source: 'backend_llm' };
        }
      } catch (err) {
        console.warn('Backend /api/assess error, falling back to client reasoner:', err);
      }
    }

    // Fallback to client-side Clinical Reasoner
    const localResult = await this.localReasoner.assessRisk(patientData, sensorFeatures);
    this.logTelemetry('INTERNAL AI', 'ClientReasoner.assessRisk', payload, localResult);
    return { data: localResult, source: 'local_engine' };
  }

  /**
   * Connects to live WebSocket for real-time ESP32 sensor stream
   */
  connectWebSocket() {
    if (this.wsSocket && (this.wsSocket.readyState === WebSocket.OPEN || this.wsSocket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.wsSocket = new WebSocket(this.wsUrl);

      this.wsSocket.onopen = () => {
        this.wsConnected = true;
        if (this.onConnectionStatusChanged) {
          this.onConnectionStatusChanged({
            backendOnline: this.isBackendOnline,
            wsConnected: true,
            httpUrl: this.httpBaseUrl
          });
        }
      };

      this.wsSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (this.onSensorDataReceived) {
            this.onSensorDataReceived(data);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      this.wsSocket.onclose = () => {
        this.wsConnected = false;
        if (this.onConnectionStatusChanged) {
          this.onConnectionStatusChanged({
            backendOnline: this.isBackendOnline,
            wsConnected: false,
            httpUrl: this.httpBaseUrl
          });
        }
      };

      this.wsSocket.onerror = (err) => {
        console.warn('WebSocket connection error:', err);
        this.wsConnected = false;
      };
    } catch (e) {
      console.warn('Cannot establish WebSocket:', e);
    }
  }

  disconnectWebSocket() {
    if (this.wsSocket) {
      this.wsSocket.close();
      this.wsSocket = null;
      this.wsConnected = false;
    }
  }
}
