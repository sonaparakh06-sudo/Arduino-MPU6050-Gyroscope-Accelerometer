#include "Wire.h"
#include "MPU6050.h"

// class default I2C address is 0x68
MPU6050 accelgyro;

int16_t ax, ay, az;
int16_t gx, gy, gz;

void setup() {
  // join I2C bus
  Wire.begin();

  Serial.begin(115200);

  // initialize device
  Serial.println("Initializing I2C devices...");
  accelgyro.initialize();
  Serial.println("Testing device connections...");
  Serial.println(accelgyro.testConnection() ? "MPU6050 connection successful" : "MPU6050 connection failed");
}

void loop() {
  // read raw accel/gyro measurements from device
  accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

  // display comma-separated accel/gyro x/y/z values for serial plotter
  Serial.print("ax:");
  Serial.print(ax);
  Serial.print(",");
  Serial.print("ay:");
  Serial.print(ay);
  Serial.print(",");
  Serial.print("az:");
  Serial.print(az);
  Serial.print(",");
  Serial.print("gx:");
  Serial.print(gx);
  Serial.print(",");
  Serial.print("gy:");
  Serial.print(gy);
  Serial.print(",");
  Serial.print("gz:");
  Serial.println(gz);
}
