/*
 * Air Guitar IMU Sensor Code
 * MPU6050 - 6-axis accelerometer/gyroscope
 * 
 * Sends wrist angle (ROLL) and strumming force (acceleration magnitude)
 * to Python via serial in format: ROLL:FORCE
 * 
 * Circuit:
 * - MPU6050 SDA -> Arduino A4 (or SDA)
 * - MPU6050 SCL -> Arduino A5 (or SCL)
 * - MPU6050 VCC -> Arduino 5V
 * - MPU6050 GND -> Arduino GND
 */

#include <Wire.h>

// MPU6050 I2C address
const int MPU_ADDR = 0x68;

// Register addresses
const int ACCEL_XOUT_H = 0x3B;
const int PWR_MGMT_1 = 0x6B;

// Raw accelerometer data
int16_t acX, acY, acZ;

void setup() {
  // Start serial communication at 115200 baud
  Serial.begin(115200);
  
  // Start I2C communication
  Wire.begin();
  
  // Initialize MPU6050
  initMPU6050();
  
  delay(500);
  Serial.println("READY");
}

void loop() {
  // Read accelerometer data
  readAccelerometer();
  
  // Calculate ROLL (wrist angle in degrees)
  // The atan2 function gives us the angle when tilting around the X axis
  // This represents the wrist rotation left/right
  // Range: -90 to +90 degrees
  float roll = atan2(acY, acZ) * 180.0 / PI;
  
  // Calculate FORCE (acceleration magnitude)
  // This represents the "strumming" intensity and speed
  // Calculated as the magnitude of the acceleration vector
  long accel_mag_squared = (long)acX*acX + (long)acY*acY + (long)acZ*acZ;
  long force = sqrt(accel_mag_squared) / 100;  // Scale down to reasonable range
  
  // Send formatted data to Python: "ROLL:FORCE\n"
  // Roll is a float (wrist angle), Force is an integer (acceleration magnitude)
  Serial.print(roll);
  Serial.print(":");
  Serial.println(force);
  
  // Wait ~16ms (60Hz sample rate)
  // This gives enough data points without overwhelming serial communication
  delay(16);
}

void initMPU6050() {
  /*
   * Initialize MPU6050 sensor
   * Clear the sleep bit to wake up the sensor
   */
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(PWR_MGMT_1);      // Power Management 1 register
  Wire.write(0);               // Write 0 to clear sleep bit (wake up)
  Wire.endTransmission(true);
  
  // Wait for stabilization
  delay(100);
}

void readAccelerometer() {
  /*
   * Read 6 bytes of accelerometer data from MPU6050
   * Data is in big-endian format (high byte first)
   */
  
  // Request starting address
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(ACCEL_XOUT_H);    // Start at ACCEL_XOUT_H (0x3B)
  Wire.endTransmission(false); // Keep connection open
  
  // Request 6 bytes (XOUT_H, XOUT_L, YOUT_H, YOUT_L, ZOUT_H, ZOUT_L)
  Wire.requestFrom(MPU_ADDR, 6, true);
  
  // Read X, Y, Z acceleration values (16-bit signed integers)
  acX = (Wire.read() << 8) | Wire.read();  // Combine two bytes into 16-bit value
  acY = (Wire.read() << 8) | Wire.read();
  acZ = (Wire.read() << 8) | Wire.read();
}
