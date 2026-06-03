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
  }

  else if (command == "LED:FAILURE") {

    led_failure();
  }

  else if (command == "LED:UNKNOWN") {

    led_unknown();
  }

  else if (command == "LED:OFF") {

    led_off();
  }

  else if (command == "C_SERVO:CENTER") {

    camera_servo_center();
  }

  else if (command.startsWith("C_SERVO:")) {

    int angle = command.substring(8).toInt();

    camera_servo_set_angle(angle);
  }
}