#pragma once
#include <Arduino.h>

const uint8_t icon_cloudy[8][12] PROGMEM = {
  {0,0,0,0,0,0,1,1,0,0,0,0},
  {0,0,0,0,0,1,0,1,0,0,0,0},
  {0,0,0,0,1,0,0,0,1,0,0,0},
  {0,0,0,1,0,0,0,0,0,1,0,0},
  {0,0,1,1,0,0,0,1,0,1,0,0},
  {0,0,1,1,1,1,1,0,1,1,0,0},
  {0,0,0,0,0,0,0,0,0,0,0,0},
  {0,0,0,0,0,0,0,0,0,0,0,0}
};

// White tones
#define ICON_PRIMARY_R 255
#define ICON_PRIMARY_G 255
#define ICON_PRIMARY_B 255
#define ICON_SECONDARY_R 255
#define ICON_SECONDARY_G 255
#define ICON_SECONDARY_B 255
