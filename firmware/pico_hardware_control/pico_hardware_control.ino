#include <FastLED.h>

#define NUM_LEDS 18
#define LED_PIN 16

CRGB leds[NUM_LEDS];

void led_on(int total_led, CRGB color) {
  FastLED.clear();

  if (total_led > NUM_LEDS) {
    total_led = NUM_LEDS;
  }

  for (int i = 0; i < total_led; i++) {
    leds[i] = color;
  }

  FastLED.show();
}

void setup() {
  Serial.begin(115200);

  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(150);
  FastLED.clear();
  FastLED.show();

  Serial.println("MAE 148 mission LED ready");
  Serial.println("Commands: success, unknown, failure, off");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "success") {
      led_on(NUM_LEDS, CRGB::Green);
      Serial.println("Status: SUCCESS");

    } else if (command == "unknown") {
      led_on(NUM_LEDS, CRGB::Blue);
      Serial.println("Status: UNKNOWN");

    } else if (command == "failure") {
      led_on(NUM_LEDS, CRGB::Red);
      Serial.println("Status: FAILURE");

    } else if (command == "off") {
      FastLED.clear();
      FastLED.show();
      Serial.println("Status: OFF");

    } else {
      Serial.println("Unknown command. Use: success, unknown, failure, off");
    }
  }
}