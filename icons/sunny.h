#pragma once
#include <Arduino.h>

const uint8_t icon_sunny[8][12] PROGMEM = {
  {0,0,1,0,0,1,1,0,0,1,0,0},
  {0,0,0,1,0,1,1,0,1,0,0,0},
  {0,0,0,0,1,0,0,1,0,0,0,0},
  {0,0,1,1,0,0,0,0,1,1,0,0},
  {0,0,1,1,0,0,0,0,1,1,0,0},
  {0,0,0,0,1,0,0,1,0,0,0,0},
  {0,0,0,1,0,1,1,0,1,0,0,0},
  {0,0,1,0,0,0,0,0,0,1,0,0}
};

// Warm yellow-orange tones
#define ICON_PRIMARY_R 255
#define ICON_PRIMARY_G 180
#define ICON_PRIMARY_B 0
#define ICON_SECONDARY_R 255
#define ICON_SECONDARY_G 220
#define ICON_SECONDARY_B 100
