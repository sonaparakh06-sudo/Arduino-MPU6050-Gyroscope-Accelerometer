/*
  Self-Leveling Platform with Tilt + Distance Display
  ---------------------------------------------------
  - MPU6050: roll & pitch via complementary filter (gyro + accelerometer)
  - Servo:   counter-rotates against roll to keep a platform level
  - HC-SR04: distance measurement
  - LCD1602 (I2C): live roll, pitch and distance

  Board: Arduino Uno
*/

#include <Wire.h>
#include <MPU6050.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

// ---------- Hardware ----------
MPU6050 mpu;                          // I2C address 0x68
LiquidCrystal_I2C lcd(0x27, 16, 2);   // I2C address 0x27
Servo levelServo;

const int TRIG_PIN  = 9;
const int ECHO_PIN  = 10;
const int SERVO_PIN = 6;

// ---------- Filter settings ----------
const float ALPHA = 0.98;             // trust gyro 98%, accelerometer 2%
const float ACCEL_SCALE = 16384.0;    // LSB per g (+/-2g range)
const float GYRO_SCALE  = 131.0;      // LSB per deg/s (+/-250 deg/s range)

// ---------- State ----------
int16_t ax, ay, az, gx, gy, gz;
float roll = 0, pitch = 0;            // degrees
float gxOffset = 0, gyOffset = 0;     // gyro bias (deg/s)
float servoAngle = 90;                // smoothed servo position
float distanceCm = -1;                // -1 = nothing detected
unsigned long lastMicros = 0;
unsigned long lastDistMs = 0, lastLcdMs = 0, lastPrintMs = 0;

// ---------- HC-SR04 ----------
float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000UL);  // 30 ms timeout
  if (duration == 0) return -1;                      // out of range
  return duration * 0.0343 / 2.0;
}

// ---------- Gyro calibration (keep the board still) ----------
void calibrateGyro() {
  const int samples = 200;
  float sumX = 0, sumY = 0;
  for (int i = 0; i < samples; i++) {
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    sumX += gx / GYRO_SCALE;
    sumY += gy / GYRO_SCALE;
    delay(3);
  }
  gxOffset = sumX / samples;
  gyOffset = sumY / samples;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Initializing...");

  Serial.println("Initializing I2C devices...");
  mpu.initialize();
  Serial.println(mpu.testConnection() ? "MPU6050 connection successful"
                                      : "MPU6050 connection failed");

  levelServo.attach(SERVO_PIN);
  levelServo.write(90);

  lcd.setCursor(0, 1);
  lcd.print("Calibrating...");
  calibrateGyro();

  // Start the filter from the accelerometer's view of the world
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  float axg = ax / ACCEL_SCALE, ayg = ay / ACCEL_SCALE, azg = az / ACCEL_SCALE;
  roll  = atan2(ayg, azg) * RAD_TO_DEG;
  pitch = atan2(-axg, sqrt(ayg * ayg + azg * azg)) * RAD_TO_DEG;

  lcd.clear();
  lastMicros = micros();
}

void loop() {
  // ----- time step -----
  unsigned long nowUs = micros();
  float dt = (nowUs - lastMicros) / 1000000.0;
  lastMicros = nowUs;

  // ----- read sensor -----
  mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
  float axg = ax / ACCEL_SCALE;
  float ayg = ay / ACCEL_SCALE;
  float azg = az / ACCEL_SCALE;
  float gxDps = gx / GYRO_SCALE - gxOffset;
  float gyDps = gy / GYRO_SCALE - gyOffset;

  // ----- angles from accelerometer (noisy but no drift) -----
  float accRoll  = atan2(ayg, azg) * RAD_TO_DEG;
  float accPitch = atan2(-axg, sqrt(ayg * ayg + azg * azg)) * RAD_TO_DEG;

  // ----- complementary filter -----
  roll  = ALPHA * (roll  + gxDps * dt) + (1.0 - ALPHA) * accRoll;
  pitch = ALPHA * (pitch + gyDps * dt) + (1.0 - ALPHA) * accPitch;

  // ----- servo: counter-rotate against roll to level the platform -----
  float target = constrain(90.0 - roll, 0, 180);
  servoAngle = 0.8 * servoAngle + 0.2 * target;      // smooth movement
  levelServo.write((int)servoAngle);

  unsigned long nowMs = millis();

  // ----- distance (every 100 ms) -----
  if (nowMs - lastDistMs >= 100) {
    lastDistMs = nowMs;
    distanceCm = readDistanceCm();
  }

  // ----- LCD (every 200 ms) -----
  if (nowMs - lastLcdMs >= 200) {
    lastLcdMs = nowMs;
    char line[17];

    snprintf(line, sizeof(line), "R:%4d P:%4d", (int)roll, (int)pitch);
    lcd.setCursor(0, 0);
    lcd.print(line);
    lcd.print("    ");

    if (distanceCm < 0) {
      snprintf(line, sizeof(line), "Dist: --- cm");
    } else {
      snprintf(line, sizeof(line), "Dist:%4d cm", (int)distanceCm);
    }
    lcd.setCursor(0, 1);
    lcd.print(line);
    lcd.print("    ");
  }

  // ----- Serial Monitor / Plotter (every 50 ms) -----
  if (nowMs - lastPrintMs >= 50) {
    lastPrintMs = nowMs;
    Serial.print("roll:");  Serial.print(roll);
    Serial.print(",pitch:"); Serial.print(pitch);
    Serial.print(",servo:"); Serial.print(servoAngle);
    Serial.print(",dist:");  Serial.println(distanceCm < 0 ? 0 : distanceCm);
  }
}
