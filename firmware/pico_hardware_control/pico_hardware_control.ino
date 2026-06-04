#include "led_controller.h"
#include "camera_servo_controller.h"
#include "command_parser.h"

void setup() {

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);

  led_begin();
  camera_servo_begin();

  led_unknown();

  Serial.println("PICO_HW_READY");
}

void loop() {

  if (Serial.available()) {

    String command =
        Serial.readStringUntil('\n');

    handle_command(command);
  }
}