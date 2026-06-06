#include <Arduino.h>
#include "command_parser.h"

#include "led_controller.h"
#include "camera_servo_controller.h"

void handle_command(String command) {

  command.trim();
  command.toUpperCase();

  if (command == "PING") {

    Serial.println("PONG");
  }

  else if (command == "LED:SUCCESS") {

    led_success();
    Serial.println("ACK:LED:SUCCESS");
  }

  else if (command == "LED:FAILURE") {

    led_failure();
    Serial.println("ACK:LED:FAILURE");
  }

  else if (command == "LED:UNKNOWN") {

    led_unknown();
    Serial.println("ACK:LED:UNKNOWN");
  }

  else if (command == "LED:OFF") {

    led_off();
    Serial.println("ACK:LED:OFF");
  }

  else if (command == "C_SERVO:CENTER") {

    camera_servo_center();
    Serial.println("ACK:C_SERVO:CENTER");
  }

  else if (command.startsWith("C_SERVO:")) {

    int angle = command.substring(8).toInt();

    camera_servo_set_angle(angle);
    Serial.println("ACK:C_SERVO:" + String(angle));
  }

  else {

    Serial.println("ERR:UNKNOWN_CMD");
  }
}
