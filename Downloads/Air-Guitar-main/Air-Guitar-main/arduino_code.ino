#include <Wire.h>

const int MPU_ADDR = 0x68;
int16_t acX, acY, acZ;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  // Wake up MPU6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);
}

void loop() {
  // Read Accelerometer
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 6, true);

  acX = Wire.read()<<8|Wire.read();
  acY = Wire.read()<<8|Wire.read();
  acZ = Wire.read()<<8|Wire.read();

  // Calculate ROLL (Wrist Angle)
  // When flat, it's 0. Tilted left is negative, right is positive.
  float roll = atan2(acY, acZ) * 180.0 / PI;

  // Calculate FORCE (Strumming magnitude)
  long force = sqrt((long)acX*acX + (long)acY*acY + (long)acZ*acZ) / 100;

  // Send to Python: "ROLL:FORCE"
  Serial.print(roll);
  Serial.print(":");
  Serial.println(force);

  delay(15); // ~60Hz sample rate
}
