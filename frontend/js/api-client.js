/**
 * CardioNav AI - REST & WebSocket API Client
 * Seamless integration with Supabase Auth, FastAPI Backend & ESP32 Hardware
 */

import { AIClinicalReasoner } from './ai-reasoner.js';

export class APIClient {
  constructor(options = {}) {
    this.httpBaseUrl = options.httpBaseUrl || 'http://localhost:8000';
    this.wsBaseUrl = options.wsBaseUrl || 'ws://localhost:8000';
    this.authToken = options.authToken || null;
    this.currentSessionId = null;
    this.isBackendOnline = false;
    this.wsSocket = null;
    this.wsConnected = false;
    this.localReasoner = new AIClinicalReasoner();

    this.onSensorDataReceived = options.onSensorDataReceived || null;
    this.onConnectionStatusChanged = options.onConnectionStatusChanged || null;
    this.telemetryLogs = [];

    this.checkHealth();
  }

  setAuthToken(token) {
    this.authToken = token;
  }

  setEndpoints(httpUrl, wsUrl) {
    this.httpBaseUrl = httpUrl.replace(/\/$/, '');
    this.wsBaseUrl = wsUrl ? wsUrl.replace(/\/$/, '') : this.wsBaseUrl;
    this.checkHealth();
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    return headers;
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
   * Starts a new screening measurement session on the FastAPI backend
   */
  async startSession(deviceId = null) {
    if (!this.isBackendOnline) {
      this.currentSessionId = 'local_session_' + Date.now();
      return { id: this.currentSessionId, status: 'active' };
    }

    try {
      const res = await fetch(`${this.httpBaseUrl}/api/sessions`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ device_id: deviceId })
      });
      if (res.ok) {
        const data = await res.json();
        this.currentSessionId = data.id;
        return data;
      }
    } catch (err) {
      console.warn('Could not start backend session:', err);
    }
    this.currentSessionId = 'fallback_session_' + Date.now();
    return { id: this.currentSessionId, status: 'active' };
  }

  /**
   * Submits patient context + sensor features for AI Clinical Risk Assessment
   */
  async runAssessment(patientData, sensorFeatures) {
    const symptoms = patientData.symptoms || [];

    // If backend is active and we have or can create a session
    if (this.isBackendOnline) {
      try {
        if (!this.currentSessionId || this.currentSessionId.startsWith('local_')) {
          await this.startSession();
        }

        // 1. Post current sensor reading to session
        await fetch(`${this.httpBaseUrl}/api/sessions/${this.currentSessionId}/readings`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({
            heart_rate: sensorFeatures.heartRate,
            hrv: sensorFeatures.hrv,
            signal_quality: sensorFeatures.signalQuality,
            spo2: sensorFeatures.spo2,
            ppg: [sensorFeatures.heartRate / 100.0]
          })
        }).catch(() => {});

        // 2. Request AI Risk Assessment
        const res = await fetch(`${this.httpBaseUrl}/api/sessions/${this.currentSessionId}/assess-risk`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({
            symptoms: symptoms,
            additional_notes: `BP: ${patientData.systolicBp}/${patientData.diastolicBp}`
          })
        });

        if (res.ok) {
          const backendData = await res.json();
          this.logTelemetry('REST POST', `/api/sessions/${this.currentSessionId}/assess-risk`, { symptoms }, backendData);

          // Merge into unified triage response matching frontend expectation
          const localFallback = await this.localReasoner.assessRisk(patientData, sensorFeatures);
          const combined = {
            ...localFallback,
            overall_risk_level: backendData.risk_level,
            backend_assessment: backendData
          };
          return { data: combined, source: `backend_${backendData.model_name || 'ai'}` };
        }
      } catch (err) {
        console.warn('Backend assess error, using client reasoner fallback:', err);
      }
    }

    // Fallback to client-side Clinical Reasoner
    const localResult = await this.localReasoner.assessRisk(patientData, sensorFeatures);
    this.logTelemetry('INTERNAL AI', 'ClientReasoner.assessRisk', patientData, localResult);
    return { data: localResult, source: 'local_engine' };
  }

  /**
   * Connects to live WebSocket for real-time ESP32 sensor stream
   */
  connectWebSocket(sessionId = null) {
    const activeSession = sessionId || this.currentSessionId || 'default';
    const targetWsUrl = `${this.wsBaseUrl}/ws/sessions/${activeSession}`;

    if (this.wsSocket && (this.wsSocket.readyState === WebSocket.OPEN || this.wsSocket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.wsSocket = new WebSocket(targetWsUrl);

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
