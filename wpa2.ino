#include <WiFiEnterprise.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include <time.h>
#include "config.h"

// --- MATRIX SETUP ---
#define PIN 23
#define MATRIX_WIDTH 145
#define MATRIX_HEIGHT 8

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(
  MATRIX_WIDTH, MATRIX_HEIGHT, PIN,
  NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG,
  NEO_GRB + NEO_KHZ800
);

// --- TIMING ---
const unsigned long dataInterval = 60000;
unsigned long lastDataFetch = 0;
unsigned long lastModeSwitch = 0;
unsigned long currentModeDuration = 0; // dynamically calculated

// --- MODES ---
enum DisplayMode {
  MODE_WEATHER,
  MODE_BUS,
  MODE_TIME,
  MODE_EXCUSE,
  MODE_MESSAGE,
  MODE_COUNT
};
DisplayMode currentMode = MODE_WEATHER;

// --- DISPLAY STATE ---
String displayText = "";
int16_t scrollX = 0;

// --- COLORS ---
uint16_t weatherColor = matrix.Color(0, 150, 255);
uint16_t timeColor    = matrix.Color(0, 255, 100);
uint16_t busColor     = matrix.Color(255, 180, 0);
uint16_t excuseColor  = matrix.Color(255, 100, 255);
uint16_t messageColor = matrix.Color(255, 255, 0);

// --- FUNCTION DECLARATIONS ---
void fetchWeather();
void fetchBusTimes();
void showTime();
void fetchExcuse();
void fetchMessage();
void nextMessage();
void updateDisplay();
void scrollText();
uint16_t getModeColor(DisplayMode mode);
unsigned long getScrollDuration(const String &text);

// --- MODE COLOR SELECTION ---
uint16_t getModeColor(DisplayMode mode) {
  switch (mode) {
    case MODE_WEATHER: return weatherColor;
    case MODE_BUS:     return busColor;
    case MODE_TIME:    return timeColor;
    case MODE_EXCUSE:  return excuseColor;
    case MODE_MESSAGE: return messageColor;
    default:           return matrix.Color(255, 255, 255);
  }
}

// --- Scroll Duration (based on text width) ---
unsigned long getScrollDuration(const String &text) {
  int16_t x1, y1;
  uint16_t w, h;
  matrix.getTextBounds(text, 0, 0, &x1, &y1, &w, &h);

  // total distance = text width + matrix width, plus a small buffer
  int totalPixels = w + matrix.width() + 20;  // +8 px padding for timing margin

  unsigned long perFrame = 50;  // matches delay(50)
  unsigned long duration = (unsigned long)totalPixels * perFrame;

  // show twice
  duration *= 2;

  // add small buffer (~½ second) for end smoothness
  duration += 500;

  return constrain(duration, 2000UL, 60000UL);
}

void setup() {
  Serial.begin(115200);
  Serial.println("Connecting to WPA2-Enterprise WiFi...");

  if (WiFiEnterprise.begin(ssid, username, password, true)) {
    Serial.println("Connected!");
    Serial.print("IP: ");
    Serial.println(WiFiEnterprise.localIP());
  } else {
    Serial.println("Connection failed!");
  }

  // Initialize NTP (Eastern Time)
  configTzTime("EST5EDT,M3.2.0,M11.1.0", "pool.ntp.org", "time.nist.gov");

  // Initialize LED Matrix
  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setBrightness(20);
  matrix.setTextColor(weatherColor);

  // Initial data fetch and display
  fetchWeather();
  updateDisplay();
  scrollX = matrix.width();
  lastDataFetch = millis();
  lastModeSwitch = millis();
  currentModeDuration = getScrollDuration(displayText);
}

void loop() {
  unsigned long now = millis();

  // --- Rotate between modes ---
  if (now - lastModeSwitch >= currentModeDuration) {
    if (currentMode == MODE_MESSAGE) {
      Serial.println("Advancing message queue before leaving message mode...");
      nextMessage();
    }

    currentMode = (DisplayMode)((currentMode + 1) % MODE_COUNT);
    updateDisplay();
    scrollX = matrix.width();

    currentModeDuration = getScrollDuration(displayText);
    lastModeSwitch = now;
  }

  // --- Refresh API data periodically ---
  if (now - lastDataFetch >= dataInterval) {
    switch (currentMode) {
      case MODE_WEATHER: fetchWeather(); break;
      case MODE_BUS:     fetchBusTimes(); break;
      case MODE_EXCUSE:  fetchExcuse(); break;
      case MODE_MESSAGE: fetchMessage(); break;
      default: break;
    }
    lastDataFetch = now;
  }

  // --- Scroll text ---
  scrollText();
  delay(50);
}

// --- Mode Switch Logic ---
void updateDisplay() {
  Serial.println();
  switch (currentMode) {
    case MODE_WEATHER: Serial.println("Mode: Weather"); fetchWeather(); break;
    case MODE_BUS:     Serial.println("Mode: Bus"); fetchBusTimes(); break;
    case MODE_TIME:    Serial.println("Mode: Time"); showTime(); break;
    case MODE_EXCUSE:  Serial.println("Mode: Excuse"); fetchExcuse(); break;
    case MODE_MESSAGE: Serial.println("Mode: Message"); fetchMessage(); break;
  }

  matrix.setTextColor(getModeColor(currentMode));
  Serial.println("[Display] " + displayText);
  scrollX = matrix.width();
}

// --- Weather ---
void fetchWeather() {
  HTTPClient http;
  http.begin(weatherPath);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    StaticJsonDocument<1024> doc;
    DeserializationError err = deserializeJson(doc, payload);
    if (!err) {
      String tempF = doc["current"]["temp_f"].as<String>();
      String condition = doc["current"]["condition"]["text"].as<String>();
      displayText = condition + ", " + tempF + "F";
    } else displayText = "Weather parse error";
  } else displayText = "Weather HTTP " + String(httpCode);

  http.end();
  Serial.println("Weather: " + displayText);
}

// --- Bus ---
void fetchBusTimes() {
  HTTPClient http;
  http.begin(busURL);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    payload.trim();
    if (payload.startsWith("\xEF\xBB\xBF")) payload.remove(0, 3);

    DynamicJsonDocument busDoc(8192);
    DeserializationError err = deserializeJson(busDoc, payload);

    if (err == DeserializationError::InvalidInput) {
      int firstBracket = payload.indexOf('[');
      int lastBracket = payload.lastIndexOf(']');
      if (firstBracket != -1 && lastBracket != -1 && lastBracket > firstBracket) {
        payload = payload.substring(firstBracket + 1, lastBracket);
        err = deserializeJson(busDoc, payload);
      }
    }

    if (!err) {
      JsonArray times = busDoc["Times"];
      if (times.isNull()) times = busDoc[0]["Times"];

      if (!times.isNull()) {
        String msg = "Bus: ";
        int count = 0;
        for (JsonObject t : times) {
          if (!t.containsKey("Seconds") || t["Seconds"].isNull()) continue;
          int sec = t["Seconds"];
          if (sec <= 0) continue;
          int min = max(1, sec / 60);
          msg += String(min) + "m ";
          if (++count >= 3) break;
        }
        displayText = count ? msg : "No valid times";
      } else displayText = "No times";
    } else displayText = "Bus parse error";
  } else displayText = "Bus HTTP " + String(httpCode);

  http.end();
  Serial.println("Bus: " + displayText);
}

// --- Excuse ---
void fetchExcuse() {
  HTTPClient http;
  http.begin(excusesURL);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, payload);
    if (!err && doc.containsKey("text")) {
      displayText = "Excuse: " + doc["text"].as<String>();
    } else displayText = "Excuse parse error";
  } else displayText = "Excuse HTTP " + String(httpCode);

  http.end();
  Serial.println("Excuse: " + displayText);
}

// --- Message ---
void fetchMessage() {
  HTTPClient http;
  http.begin(messageURL);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    payload.trim();
    displayText = payload;
  } else displayText = "Msg HTTP " + String(httpCode);

  http.end();
  Serial.println("Message: " + displayText);
}

// --- Next Message (advance queue when leaving message mode) ---
void nextMessage() {
  HTTPClient http;
  http.begin(nextURL);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    payload.trim();
    displayText = payload;
    scrollX = matrix.width();
    Serial.println("Next message: " + displayText);
  } else {
    Serial.print("Next message HTTP error: ");
    Serial.println(httpCode);
  }
  http.end();
}

// --- Time ---
void showTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    displayText = "No time data";
    return;
  }
  char buf[16];
  strftime(buf, sizeof(buf), "%I:%M%p", &timeinfo);
  displayText = String(buf);
  Serial.println("Time: " + displayText);
}

// --- Scroll ---
void scrollText() {
  matrix.fillScreen(0);
  matrix.setCursor(scrollX, 0);
  matrix.print(displayText);
  matrix.show();

  scrollX--;
  if (scrollX < -((int)displayText.length() * 6)) {
    scrollX = matrix.width();
  }
}
