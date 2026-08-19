/*
  ============================================================
  AI HEALTH MONITOR - ESP32 + MAX30102
  ============================================================

  Hardware:
    ESP32
    MAX30102
    LED + 220 ohm resistor

  MAX30102:
    VCC  -> 3.3V
    GND  -> GND
    SDA  -> GPIO21
    SCL  -> GPIO22

  LED:
    GPIO2 -> 220 ohm resistor -> LED anode (+)
    LED cathode (-) -> GND

  LED LOGIC:
    Finger detected     -> LED ON continuously
    No finger detected  -> LED blinks

  OLED:
    NOT USED
*/

// ============================================================
// LIBRARIES
// ============================================================

#include <Wire.h>
#include <MAX30105.h>
#include "spo2_algorithm.h"

// ============================================================
// PIN CONFIGURATION
// ============================================================

#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

#define LED_PIN 5

#define MAX30102_ADDRESS 0x57

// ============================================================
// MAX30102 CONFIGURATION
// ============================================================

#define SENSOR_SAMPLE_RATE 100
#define SENSOR_SAMPLE_AVERAGE 4

#define SENSOR_LED_BRIGHTNESS 60
#define SENSOR_LED_MODE 2

#define SENSOR_PULSE_WIDTH 411
#define SENSOR_ADC_RANGE 4096

// ============================================================
// FINGER DETECTION
// ============================================================

#define FINGER_DETECT_THRESHOLD 50000

// ============================================================
// BUFFER
// ============================================================

#define BUFFER_LENGTH 100

uint32_t irBuffer[BUFFER_LENGTH];
uint32_t redBuffer[BUFFER_LENGTH];

int bufferCount = 0;

// ============================================================
// SENSOR
// ============================================================

MAX30105 particleSensor;

bool sensorReady = false;

// ============================================================
// VITALS
// ============================================================

int32_t heartRate = 0;
int8_t validHeartRate = 0;

int32_t spo2 = 0;
int8_t validSpO2 = 0;

bool fingerDetected = false;

// ============================================================
// TIMERS
// ============================================================

unsigned long lastLedToggle = 0;
unsigned long lastRawPrint = 0;
unsigned long lastStatusPrint = 0;

const unsigned long LED_BLINK_INTERVAL = 500;
const unsigned long RAW_PRINT_INTERVAL = 500;
const unsigned long STATUS_PRINT_INTERVAL = 1000;

bool ledState = false;

// ============================================================
// I2C SCANNER
// ============================================================

void scanI2C()
{
  Serial.println();
  Serial.println("[I2C] Scanning...");

  int devicesFound = 0;

  for (uint8_t address = 1; address < 127; address++)
  {
    Wire.beginTransmission(address);

    uint8_t error = Wire.endTransmission();

    if (error == 0)
    {
      Serial.print("[I2C] Device found at 0x");

      if (address < 16)
        Serial.print("0");

      Serial.println(address, HEX);

      devicesFound++;
    }
  }

  if (devicesFound == 0)
  {
    Serial.println("[I2C] No devices found!");
  }
  else
  {
    Serial.print("[I2C] Devices found: ");
    Serial.println(devicesFound);
  }

  Serial.println();
}

// ============================================================
// MAX30102 INITIALIZATION
// ============================================================

bool initializeMAX30102()
{
  Serial.println("[MAX30102] Initializing...");

  if (!particleSensor.begin(
        Wire,
        I2C_SPEED_FAST,
        MAX30102_ADDRESS))
  {
    Serial.println("[MAX30102] ERROR: Sensor not detected!");

    Serial.println("[MAX30102] Check wiring:");
    Serial.println("  VCC -> 3.3V");
    Serial.println("  GND -> GND");
    Serial.println("  SDA -> GPIO21");
    Serial.println("  SCL/SCK -> GPIO22");

    return false;
  }

  Serial.println("[MAX30102] Sensor detected.");

  particleSensor.setup(
    SENSOR_LED_BRIGHTNESS,
    SENSOR_SAMPLE_AVERAGE,
    SENSOR_LED_MODE,
    SENSOR_SAMPLE_RATE,
    SENSOR_PULSE_WIDTH,
    SENSOR_ADC_RANGE
  );

  particleSensor.setPulseAmplitudeGreen(0);

  Serial.println("[MAX30102] Configuration complete.");

  return true;
}

// ============================================================
// CLEAR BUFFER
// ============================================================

void clearBuffers()
{
  for (int i = 0; i < BUFFER_LENGTH; i++)
  {
    irBuffer[i] = 0;
    redBuffer[i] = 0;
  }

  bufferCount = 0;

  heartRate = 0;
  spo2 = 0;

  validHeartRate = 0;
  validSpO2 = 0;
}

// ============================================================
// FINGER DETECTION
// ============================================================

bool detectFinger(uint32_t irValue)
{
  return irValue > FINGER_DETECT_THRESHOLD;
}

// ============================================================
// LED CONTROL
// ============================================================

void updateLED()
{
  // ==========================================================
  // FINGER DETECTED
  // LED MUST STAY ON
  // ==========================================================

  if (fingerDetected)
  {
    digitalWrite(LED_PIN, HIGH);

    ledState = true;

    return;
  }

  // ==========================================================
  // NO FINGER
  // LED BLINKS
  // ==========================================================

  if (millis() - lastLedToggle >= LED_BLINK_INTERVAL)
  {
    lastLedToggle = millis();

    ledState = !ledState;

    digitalWrite(
      LED_PIN,
      ledState ? HIGH : LOW
    );
  }
}

// ============================================================
// RAW DATA OUTPUT
// ============================================================

void printRawData(
  uint32_t irValue,
  uint32_t redValue)
{
  if (millis() - lastRawPrint < RAW_PRINT_INTERVAL)
    return;

  lastRawPrint = millis();

  Serial.print("[RAW] IR=");
  Serial.print(irValue);

  Serial.print(" RED=");
  Serial.print(redValue);

  Serial.print(" Finger=");

  if (fingerDetected)
    Serial.println("YES");
  else
    Serial.println("NO");
}

// ============================================================
// CALCULATE HR + SPO2
// ============================================================

void calculateVitals()
{
  if (bufferCount < BUFFER_LENGTH)
    return;

  maxim_heart_rate_and_oxygen_saturation(
    irBuffer,
    BUFFER_LENGTH,
    redBuffer,
    &spo2,
    &validSpO2,
    &heartRate,
    &validHeartRate
  );

  // Validate heart rate
  if (heartRate < 30 || heartRate > 200)
  {
    validHeartRate = 0;
  }

  // Validate SpO2
  if (spo2 < 50 || spo2 > 100)
  {
    validSpO2 = 0;
  }
}

// ============================================================
// STATUS OUTPUT
// ============================================================

void printStatus()
{
  if (millis() - lastStatusPrint < STATUS_PRINT_INTERVAL)
    return;

  lastStatusPrint = millis();

  Serial.println();
  Serial.println("--------------------------------");

  if (!fingerDetected)
  {
    Serial.println("[FINGER] Not detected");

    Serial.println("[SENSOR] HR=--");
    Serial.println("[SENSOR] SpO2=--");
    Serial.println("[SENSOR] Signal=NO FINGER");
  }
  else
  {
    Serial.println("[FINGER] Detected");

    if (validHeartRate)
    {
      Serial.print("[SENSOR] HR=");
      Serial.print(heartRate);
      Serial.println(" BPM");
    }
    else
    {
      Serial.println("[SENSOR] HR=--");
    }

    if (validSpO2)
    {
      Serial.print("[SENSOR] SpO2=");
      Serial.print(spo2);
      Serial.println("%");
    }
    else
    {
      Serial.println("[SENSOR] SpO2=--");
    }

    if (validHeartRate && validSpO2)
    {
      Serial.println("[SENSOR] Signal=GOOD");
    }
    else
    {
      Serial.println("[SENSOR] Signal=COLLECTING");
    }
  }

  Serial.print("[BUFFER] ");
  Serial.print(bufferCount);
  Serial.print("/");
  Serial.println(BUFFER_LENGTH);

  Serial.println("--------------------------------");
}

// ============================================================
// READ MAX30102
// ============================================================

void readMAX30102()
{
  if (!sensorReady)
    return;

  particleSensor.check();

  while (particleSensor.available())
  {
    uint32_t irValue =
      particleSensor.getFIFOIR();

    uint32_t redValue =
      particleSensor.getFIFORed();

    // --------------------------------------------------------
    // Detect finger
    // --------------------------------------------------------

    fingerDetected =
      detectFinger(irValue);

    // --------------------------------------------------------
    // Finger detected
    // --------------------------------------------------------

    if (fingerDetected)
    {
      if (bufferCount < BUFFER_LENGTH)
      {
        irBuffer[bufferCount] = irValue;
        redBuffer[bufferCount] = redValue;

        bufferCount++;
      }
      else
      {
        // Shift old samples
        for (int i = 0;
             i < BUFFER_LENGTH - 1;
             i++)
        {
          irBuffer[i] =
            irBuffer[i + 1];

          redBuffer[i] =
            redBuffer[i + 1];
        }

        // Add newest sample
        irBuffer[BUFFER_LENGTH - 1] =
          irValue;

        redBuffer[BUFFER_LENGTH - 1] =
          redValue;
      }

      // Calculate vitals when buffer is full
      if (bufferCount >= BUFFER_LENGTH)
      {
        calculateVitals();
      }
    }

    // --------------------------------------------------------
    // Finger removed
    // --------------------------------------------------------

    else
    {
      clearBuffers();

      validHeartRate = 0;
      validSpO2 = 0;
    }

    // --------------------------------------------------------
    // Print raw data
    // --------------------------------------------------------

    printRawData(
      irValue,
      redValue
    );

    // --------------------------------------------------------
    // Move to next sample
    // --------------------------------------------------------

    particleSensor.nextSample();
  }
}

// ============================================================
// SETUP
// ============================================================

void setup()
{
  Serial.begin(115200);

  delay(500);

  // ==========================================================
  // LED SETUP
  // ==========================================================

  pinMode(
    LED_PIN,
    OUTPUT
  );

  // Keep GPIO2 LOW during boot
  digitalWrite(
    LED_PIN,
    LOW
  );

  // ==========================================================
  // STARTUP LED TEST
  // ==========================================================

  delay(300);

  digitalWrite(
    LED_PIN,
    HIGH
  );

  delay(1000);

  digitalWrite(
    LED_PIN,
    LOW
  );

  // ==========================================================
  // STARTUP MESSAGE
  // ==========================================================

  Serial.println();
  Serial.println("================================");
  Serial.println("AI HEALTH MONITOR");
  Serial.println("ESP32 + MAX30102");
  Serial.println("================================");

  Serial.println("[BOOT] ESP32 starting");

  // ==========================================================
  // I2C
  // ==========================================================

  Serial.println("[I2C] Initializing...");

  Wire.begin(
    I2C_SDA_PIN,
    I2C_SCL_PIN
  );

  Wire.setClock(400000);

  scanI2C();

  // ==========================================================
  // MAX30102
  // ==========================================================

  sensorReady =
    initializeMAX30102();

  if (sensorReady)
  {
    Serial.println("[MAX30102] READY");

    clearBuffers();

    Serial.println();
    Serial.println("================================");
    Serial.println("PLACE YOUR FINGER ON MAX30102");
    Serial.println("KEEP FINGER STEADY");
    Serial.println("================================");
  }
  else
  {
    Serial.println();
    Serial.println("[ERROR] MAX30102 is not ready.");
    Serial.println("[ERROR] Check wiring and power.");
  }

  Serial.println();
  Serial.println("[READY] System ready.");
}

// ============================================================
// MAIN LOOP
// ============================================================

void loop()
{
  // Read MAX30102
  readMAX30102();

  // Update LED based ONLY on finger detection
  updateLED();

  // Print sensor status
  printStatus();

  delay(5);
}