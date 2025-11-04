#pragma once
#include <Arduino.h>

const uint8_t icon_fog[8][12] PROGMEM = {
  {0,0,0,0,0,0,0,0,0,0,0,0},
  {0,1,1,1,1,1,1,1,1,1,1,0},
  {0,0,0,0,0,0,0,0,0,0,0,0},
  {0,1,1,1,1,1,1,1,1,1,1,0},
  {0,0,0,0,0,0,0,0,0,0,0,0},
  {0,1,1,1,1,1,1,1,1,1,1,0},
  {0,0,0,0,0,0,0,0,0,0,0,0},
  {0,1,1,1,1,1,1,1,1,1,1,0}
};

// Subtle gray tones
#define ICON_PRIMARY_R 180
#define ICON_PRIMARY_G 180
#define ICON_PRIMARY_B 180
#define ICON_SECONDARY_R 220
#define ICON_SECONDARY_G 220
#define ICON_SECONDARY_B 220
