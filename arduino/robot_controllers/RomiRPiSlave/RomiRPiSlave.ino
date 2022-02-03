#include <Servo.h>
#include <Romi32U4.h>
#include <PololuRPiSlave.h>

/* This example program shows how to make the Romi 32U4 Control Board 
 * into a Raspberry Pi I2C slave.  The RPi and Romi 32U4 Control Board can
 * exchange data bidirectionally, allowing each device to do what it
 * does best: high-level programming can be handled in a language such
 * as Python on the RPi, while the Romi 32U4 Control Board takes charge 
 * of motor control, analog inputs, and other low-level I/O.
 *
 * The example and libraries are available for download at:
 *
 * https://github.com/pololu/pololu-rpi-slave-arduino-library
 *
 * You will need the corresponding Raspberry Pi code, which is
 * available in that repository under the pi/ subfolder.  The Pi code
 * sets up a simple Python-based web application as a control panel
 * for your Raspberry Pi robot.
 */

// Custom data structure that we will use for interpreting the buffer.
// We recommend keeping this under 64 bytes total.  If you change the
// data format, make sure to update the corresponding code in
// a_star.py on the Raspberry Pi.

struct Data
{
  int16_t leftMotor, rightMotor;
  int16_t panRight, panDown;
  uint16_t batteryMillivolts;
};

PololuRPiSlave<struct Data,5> slave;
PololuBuzzer buzzer;
Romi32U4Motors motors;
Romi32U4ButtonA buttonA;
Romi32U4ButtonB buttonB;
Romi32U4ButtonC buttonC;
Romi32U4Encoders encoders;

Servo LEFT_RIGHT_PAN_SERVO;
Servo UP_DOWN_PAN_SERVO;
int LEFT_RIGHT_PAN_PIN = A0;
int UP_DOWN_PAN_PIN = A2;

struct Data lastBuffer;

void setup()
{
  // Set up the slave at I2C address 20.
  slave.init(20);

  // Play startup sound.
  buzzer.play("v10>>g16>>>c16");

  LEFT_RIGHT_PAN_SERVO.attach(LEFT_RIGHT_PAN_PIN);
  UP_DOWN_PAN_SERVO.attach(UP_DOWN_PAN_PIN);

}

bool isValidMotorValue(int val) {
  return -128 <= val && val <= 127;
}

bool isValidPanValue(int val) {
  return 0 <= val && val <= 180;
}

void loop()
{
  // Call updateBuffer() before using the buffer, to get the latest
  // data including recent master writes.
  slave.updateBuffer();

  // Change this to readBatteryMillivoltsLV() for the LV model.
  slave.buffer.batteryMillivolts = readBatteryMillivolts();

  // READING the buffer is allowed before or after finalizeWrites().
  if (slave.buffer.leftMotor != lastBuffer.leftMotor ||
      slave.buffer.rightMotor != lastBuffer.rightMotor) {
    if (isValidMotorValue(slave.buffer.leftMotor) &&
        isValidMotorValue(slave.buffer.rightMotor)) {
      Serial.print("Left motor:");
      Serial.println(slave.buffer.leftMotor);
      Serial.print("Right motor:");
      Serial.println(slave.buffer.rightMotor);
      motors.setSpeeds(slave.buffer.leftMotor, slave.buffer.rightMotor);
    }
  }
  if (slave.buffer.panRight != lastBuffer.panRight) {
    if (isValidPanValue(slave.buffer.panRight)) {
      Serial.print("Pan right:");
      Serial.println(slave.buffer.panRight);
      LEFT_RIGHT_PAN_SERVO.write(slave.buffer.panRight);
    }
  }
  if (slave.buffer.panDown != lastBuffer.panDown) {
    if (isValidPanValue(slave.buffer.panDown)) {
      Serial.print("Pan down:");
      Serial.println(slave.buffer.panDown);
      UP_DOWN_PAN_SERVO.write(slave.buffer.panDown);
    }
  }

  lastBuffer.leftMotor = slave.buffer.leftMotor;
  lastBuffer.rightMotor = slave.buffer.rightMotor;
  lastBuffer.panRight = slave.buffer.panRight;
  lastBuffer.panDown = slave.buffer.panDown;
  // When you are done WRITING, call finalizeWrites() to make modified
  // data available to I2C master.
  slave.finalizeWrites();

  
  
}
