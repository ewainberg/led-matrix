#pragma once
#include "sunny.h"
#include "rain.h"
#include "lightning.h"
#include "fog.h"
#include "cloudy.h"

struct WeatherIconMap {
  const char* condition;
  const uint8_t (*icon)[12];
  uint8_t r1, g1, b1;
  uint8_t r2, g2, b2;
};

const WeatherIconMap weatherIcons[] = {
  {"Sunny", icon_sunny, 255,180,0, 255,220,100},
  {"Clear", icon_sunny, 255,180,0, 255,220,100},
  {"Rain", icon_rain, 255,255,255, 0,120,255},
  {"Showers", icon_rain, 255,255,255, 0,120,255},
  {"Thunderstorm", icon_lightning, 255,255,0, 255,200,0},
  {"Storm", icon_lightning, 255,255,0, 255,200,0},
  {"Fog", icon_fog, 180,180,180, 220,220,220},
  {"Mist", icon_fog, 180,180,180, 220,220,220},
  {"Cloudy", icon_cloudy, 255,255,255, 255,255,255},
  {"Overcast", icon_cloudy, 255,255,255, 255,255,255}
};
