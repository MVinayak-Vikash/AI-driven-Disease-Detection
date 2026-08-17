"""
CardioNav AI - Local Development & Mock Backend Server
VITSIH-26: AI Early-Risk & Referral Navigator

Zero-dependency Python 3 HTTP Server.
Serves frontend files + provides mock endpoints for /api/sensor/ppg and /api/assess.
"""

import http.server
import socketserver
import os
import json
import webbrowser
import sys

PORT = 5173
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CardioNavHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "CardioNav AI"}).encode('utf-8'))
            return
        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8'))
        except Exception:
            body = {}

        if self.path == '/api/sensor/ppg':
            # Section 10 API Ingestion
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response_data = {
                "status": "ingested",
                "device_id": body.get("device_id", "ESP32_01"),
                "hr": body.get("bpm", 82),
                "spo2": body.get("spo2", 97),
                "sqi": 0.94
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        elif self.path == '/api/assess':
            # Section 5 & 11 LLM Output Contract
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            patient = body.get("patient", {})
            sensor = body.get("sensor", {})
            symptoms = body.get("symptoms", [])

            hr = sensor.get("heart_rate", 75)
            irreg = sensor.get("rhythm_irregularity", 0.1)

            is_high = irreg > 0.6 or "chest_discomfort" in symptoms or hr > 105
            risk_level = "HIGH" if is_high else "LOW"

            assessment_response = {
                "risk_level": risk_level,
                "conditions_of_concern": [
                    {
                        "condition": "possible_arrhythmia" if is_high else "normative_sinus_rhythm",
                        "label": "Suspected Arrhythmia / Atrial Fibrillation" if is_high else "Normal Sinus Rhythm",
                        "risk": 0.78 if is_high else 0.08,
                        "icdCode": "I48.91" if is_high else "Z00.00"
                    }
                ],
                "evidence": [
                    f"Heart rate: {hr} BPM",
                    f"Rhythm irregularity: {irreg}",
                    f"Reported symptoms: {', '.join(symptoms) if symptoms else 'None'}"
                ],
                "confidence": 0.84,
                "recommended_action": "physician_evaluation" if is_high else "routine_wellness_monitoring",
                "specialist": "cardiology" if is_high else "general_physician",
                "urgency_tier": "Urgent: Cardiology Evaluation within 48h" if is_high else "Routine: Annual Preventive",
                "clinical_summary": "Decision-support evaluation based on multi-modal sensor and symptom fusion."
            }
            self.wfile.write(json.dumps(assessment_response).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CardioNavHTTPHandler) as httpd:
        print("=" * 65)
        print("🫀 CardioNav AI - VITSIH-26 Clinical Decision Support Platform")
        print("=" * 65)
        print(f"🚀 Server running locally at: http://localhost:{PORT}")
        print(f"📁 Serving directory: {DIRECTORY}")
        print(f"📡 Mock REST Endpoints available:")
        print(f"   • GET  http://localhost:{PORT}/health")
        print(f"   • POST http://localhost:{PORT}/api/sensor/ppg")
        print(f"   • POST http://localhost:{PORT}/api/assess")
        print("=" * 65)
        print("Press Ctrl+C to stop the server.")

        # Open in default browser automatically
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")
            httpd.server_close()

if __name__ == '__main__':
    run_server()
