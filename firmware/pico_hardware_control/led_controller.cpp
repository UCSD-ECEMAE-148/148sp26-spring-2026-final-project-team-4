#include "led_controller.h"
#include "config.h"

CRGB leds[NUM_LEDS];

void led_begin() {
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(150);
  led_off();
}

void led_success() {
  fill_solid(leds, NUM_LEDS, CRGB::Green);
  FastLED.show();
}

void led_failure() {
  fill_solid(leds, NUM_LEDS, CRGB::Red);
  FastLED.show();
}

void led_unknown() {
  fill_solid(leds, NUM_LEDS, CRGB::Blue);
  FastLED.show();
}

void led_off() {
  FastLED.clear();
  FastLED.show();
}