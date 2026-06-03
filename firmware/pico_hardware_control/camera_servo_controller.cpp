#include <Servo.h>

#include "camera_servo_controller.h"
#include "config.h"

Servo camera_servo;

const int MIN_PULSE = 500;
const int MAX_PULSE = 2500;

void camera_servo_begin() {
  camera_servo.attach(CAMERA_SERVO_PIN);
  camera_servo_center();
}

void camera_servo_set_angle(int angle) {

  angle = constrain(angle, -50, 50);

  int pulse =
      map(angle, -135, 135,
          MIN_PULSE, MAX_PULSE);

  camera_servo.writeMicroseconds(pulse);
}

void camera_servo_center() {
  camera_servo_set_angle(0);
  Serial.println("ACK:C_SERVO:CENTER");
}