# 🔌 ESP32 MAX30102 Firmware Guide

This directory contains the firmware for streaming real-time optical PPG and physiological telemetry from an **ESP32 Dev Module** with a **MAX30102 / MAX30105** sensor to the FastAPI backend.

---

## 🛠️ Hardware Wiring

| ESP32 Pin | MAX30102 Pin | Notes |
|:---|:---|:---|
| **3V3** | VIN / VCC | 3.3V Power |
| **GND** | GND | Ground |
| **GPIO 21** | SDA | I2C Data |
| **GPIO 22** | SCL | I2C Clock |

---

## 📦 Required Arduino IDE Libraries
1. `SparkFun MAX3010x Sensor Library` (Install via Arduino Library Manager)
2. `WiFi` (Built-in ESP32 core)
3. `HTTPClient` (Built-in ESP32 core)

---

## 🔑 Setup Instructions
1. Register a new device in the dashboard (`POST /api/devices`). Note your `device_uid` and `generated_token`.
2. Open `esp32_max30102.ino` in Arduino IDE or VS Code PlatformIO.
3. Update `WIFI_SSID`, `WIFI_PASSWORD`, `BACKEND_URL`, `DEVICE_UID`, and `DEVICE_TOKEN`.
4. Flash to your ESP32 board at 115200 baud.
5. Place a fingertip gently over the MAX30102 sensor optical window.
6. The sensor will automatically authenticate and stream telemetry to your active session.
