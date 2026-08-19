// Configuration for AI Health Monitor Hardware Firmware
// ESP32 + MAX30102 + LED

#pragma once

// ============================================================
// HARDWARE CONFIGURATION
// ============================================================

// I2C Configuration
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define I2C_FREQ_HZ 400000

// LED Configuration (GPIO2 - Active High)
#define LED_PIN 2
#define LED_ACTIVE_HIGH true

// MAX30102 I2C Address
#define MAX30102_I2C_ADDRESS 0x57

// ============================================================
// SENSOR CONFIGURATION
// ============================================================

// Sensor Sampling
#define SENSOR_SAMPLE_RATE 25  // Hz
#define HEART_RATE_BUFFER_SIZE 100  // 4 seconds @ 25Hz
#define SPO2_SAMPLE_COUNT 100  // Samples for SpO2 calculation

// Sensor LED Current (0-0x1F, ~0-25mA)
#define MAX30102_LED_CURRENT 0x1F  // ~6.4mA

// Sensor Sample Rate: 0=50, 1=100, 2=200, 3=400, 4=800, 5=1000, 6=1600, 7=3200
#define MAX30102_SAMPLE_RATE 3  // 400 Hz

// Sensor Pulse Width: 0=69us, 1=118us, 2=215us, 3=411us
#define MAX30102_PULSE_WIDTH 3  // 411us

// Sensor ADC Range: 0=2048, 1=4096, 2=8192, 3=16384
#define MAX30102_ADC_RANGE 3  // 16384 nA

// ============================================================
// DEMO MODE
// ============================================================

// Set to true for synthetic readings, false for real sensor
#define DEMO_MODE false

// Default Demo Values
#define DEMO_HR 72
#define DEMO_SPO2 98
#define DEMO_QUALITY 0.94

// ============================================================
// LED BLINK PATTERNS (milliseconds)
// ============================================================

#define LED_STARTUP_FLASH 200
#define LED_HEARTBEAT_ON 200
#define LED_HEARTBEAT_OFF 800
#define LED_ERROR_ON 100
#define LED_ERROR_OFF 100

// ============================================================
// SENSOR VALIDATION THRESHOLDS
// ============================================================

// Finger detection: IR DC threshold
#define FINGER_DETECT_THRESHOLD 50000

// Minimum signal variance for valid signal
#define SIGNAL_VARIANCE_THRESHOLD 1000

// Valid heart rate range (BPM)
#define HR_MIN_VALID 30
#define HR_MAX_VALID 200

// Minimum interval between beats (milliseconds)
#define MIN_BEAT_INTERVAL 250  // ~240 BPM max

// ============================================================
// SERIAL CONFIGURATION
// ============================================================

#define SERIAL_BAUD 115200
