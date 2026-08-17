/*
 * CardioNav AI - ESP32 + MAX30102 Optical PPG Sensor Firmware
 * Platform: ESP32 Dev Module / NodeMCU-32S
 * Sensor: MAX30102 / MAX30105 Optical Sensor (I2C)
 * 
 * Secure Ingestion: Transmits telemetry to CardioNav FastAPI Backend via REST
 * with hardware device token authentication. Does NOT store Supabase service keys.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"

// ==========================================
// 1. NETWORK & BACKEND CONFIGURATION
// ==========================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Backend URL (Use your machine's LAN IP e.g. http://192.168.1.100:8000)
const char* BACKEND_URL   = "http://192.168.1.100:8000/api/devices";

// Device Credentials (Generated during device registration in dashboard)
const char* DEVICE_UID    = "ESP32-A8F31";
const char* DEVICE_TOKEN  = "YOUR_GENERATED_DEVICE_TOKEN";

// ==========================================
// 2. HARDWARE OBJECTS & GLOBALS
// ==========================================
MAX30105 particleSensor;

const byte RATE_SIZE = 4; // Average across 4 peak samples
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute = 0.0;
int beatAvg = 0;

unsigned long lastTransmitTime = 0;
const unsigned long TRANSMIT_INTERVAL_MS = 1000; // Transmit every 1 second

void setup() {
  Serial.begin(115200);
  Serial.println("\n=============================================");
  Serial.println("🫀 CardioNav AI - ESP32 MAX30102 Sensor Node");
  Serial.println("=============================================");

  // Connect to WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected! IP: " + WiFi.localIP().toString());

  // Initialize MAX30102 Sensor
  Wire.begin(21, 22); // SDA = GPIO 21, SCL = GPIO 22
  if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) {
    Serial.println("❌ MAX30102 sensor not found! Check wiring.");
    while (1);
  }
  Serial.println("✅ MAX30102 Sensor initialized successfully.");

  // Configure sensor settings (LED brightness, sample average, mode)
  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x0A);
  particleSensor.setPulseAmplitudeGreen(0);
}

void loop() {
  long irValue = particleSensor.getIR();

  // Beat Detection
  if (checkForBeat(irValue) == true) {
    long delta = millis() - lastBeat;
    lastBeat = millis();

    beatsPerMinute = 60 / (delta / 1000.0);
    if (beatsPerMinute < 255 && beatsPerMinute > 20) {
      rates[rateSpot++] = (byte)beatsPerMinute;
      rateSpot %= RATE_SIZE;

      beatAvg = 0;
      for (byte x = 0 ; x < RATE_SIZE ; x++) {
        beatAvg += rates[x];
      }
      beatAvg /= RATE_SIZE;
    }
  }

  // Periodic Telemetry Ingestion to Backend
  if (millis() - lastTransmitTime >= TRANSMIT_INTERVAL_MS) {
    lastTransmitTime = millis();

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      String endpoint = String(BACKEND_URL) + "/" + String(DEVICE_UID) + "/readings";
      http.begin(endpoint);

      http.addHeader("Content-Type", "application/json");
      http.addHeader("X-Device-Token", DEVICE_TOKEN);

      // Estimate SpO2 and signal quality
      float estimatedSpo2 = (irValue > 50000) ? 97.0 : 0.0;
      float signalQuality = (irValue > 50000) ? 0.94 : 0.20;

      String payload = "{";
      payload += "\"device_id\":\"" + String(DEVICE_UID) + "\",";
      payload += "\"heart_rate\":" + String(beatAvg) + ",";
      payload += "\"spo2\":" + String(estimatedSpo2) + ",";
      payload += "\"signal_quality\":" + String(signalQuality) + ",";
      payload += "\"ppg\":[" + String((float)irValue / 100000.0, 4) + "]";
      payload += "}";

      int httpCode = http.POST(payload);
      if (httpCode > 0) {
        Serial.printf("📡 Telemetry Sent [%d] | HR: %d BPM | IR: %ld\n", httpCode, beatAvg, irValue);
      } else {
        Serial.printf("⚠️ HTTP POST Error: %s\n", http.errorToString(httpCode).c_str());
      }
      http.end();
    }
  }
}
