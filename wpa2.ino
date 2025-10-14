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
#define MATRIX_WIDTH 32
#define MATRIX_HEIGHT 8

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(
  MATRIX_WIDTH, MATRIX_HEIGHT, PIN,
  NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG,
  NEO_GRB + NEO_KHZ800
);

// --- TIMING ---
const unsigned long dataInterval = 60000;
const unsigned long modeInterval = 25000;
unsigned long lastDataFetch = 0;
unsigned long lastModeSwitch = 0;

// --- MODES ---
enum DisplayMode {
  MODE_WEATHER,
  MODE_BUS,
  MODE_TIME,
  MODE_EXCUSE,
  MODE_COUNT
};
DisplayMode currentMode = MODE_WEATHER;

String displayText = "";
int16_t scrollX = 0;

// --- COLORS ---
uint16_t weatherColor = matrix.Color(0, 150, 255);   // cool blue
uint16_t timeColor    = matrix.Color(0, 255, 100);   // green
uint16_t busColor     = matrix.Color(255, 180, 0);   // warm orange
uint16_t excuseColor  = matrix.Color(255, 100, 255); // purple

// --- FUNCTION DECLARATIONS ---
void fetchWeather();
void fetchBusTimes();
void showTime();
void fetchExcuse();
void updateDisplay();
void scrollText();

uint16_t getModeColor(DisplayMode mode) {
  switch (mode) {
    case MODE_WEATHER: return weatherColor;
    case MODE_BUS:     return busColor;
    case MODE_TIME:    return timeColor;
    case MODE_EXCUSE:  return excuseColor;
    default:           return matrix.Color(255, 255, 255);
  }
}

void setup() {
  Serial.begin(115200);

  // Connect to WPA2-Enterprise Wi-Fi
  Serial.println("Connecting to WPA2-Enterprise WiFi...");
  if (WiFiEnterprise.begin(ssid, username, password, true)) {
    Serial.println("Connected!");
    Serial.print("IP: ");
    Serial.println(WiFiEnterprise.localIP());
  } else {
    Serial.println("Connection failed!");
  }

  // Initialize NTP (EST)
  configTime(-5 * 3600, 3600, "pool.ntp.org", "time.nist.gov");

  // Initialize LED Matrix
  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setBrightness(20);
  matrix.setTextColor(matrix.Color(0, 150, 255));

  // Initial data fetch
  fetchWeather();
  updateDisplay();
  scrollX = matrix.width();
  lastDataFetch = millis();
  lastModeSwitch = millis();
}

void loop() {
  unsigned long now = millis();

  // Rotate between modes
  if (now - lastModeSwitch >= modeInterval) {
    currentMode = (DisplayMode)((currentMode + 1) % MODE_COUNT);
    updateDisplay();
    lastModeSwitch = now;
  }

  // Refresh API data
  if (now - lastDataFetch >= dataInterval) {
    if (currentMode == MODE_WEATHER) fetchWeather();
    else if (currentMode == MODE_BUS) fetchBusTimes();
    else if (currentMode == MODE_EXCUSE) fetchExcuse();
    lastDataFetch = now;
  }

  scrollText();
  delay(75);
}

// --- Mode Switch Logic ---
void updateDisplay() {
  Serial.println();
  switch (currentMode) {
    case MODE_WEATHER:
      Serial.println("Mode: Weather");
      fetchWeather();
      break;
    case MODE_BUS:
      Serial.println("Mode: Bus");
      fetchBusTimes();
      break;
    case MODE_TIME:
      Serial.println("Mode: Time");
      showTime();
      break;
    case MODE_EXCUSE:
      Serial.println("Mode: Excuse");
      fetchExcuse();
      break;
  }

  matrix.setTextColor(getModeColor(currentMode)); // Set color based on mode
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
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      String tempF = doc["current"]["temp_f"].as<String>();
      String condition = doc["current"]["condition"]["text"].as<String>();
      displayText = condition + ", " + tempF + "F";
      Serial.println("Weather: " + displayText);
    } else {
      displayText = "Weather parse error";
      Serial.println("Weather JSON error");
    }
  } else {
    displayText = "Weather HTTP " + String(httpCode);
    Serial.println(displayText);
  }

  http.end();
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
    DeserializationError error = deserializeJson(busDoc, payload);

    if (error == DeserializationError::InvalidInput) {
      int firstBracket = payload.indexOf('[');
      int lastBracket = payload.lastIndexOf(']');
      if (firstBracket != -1 && lastBracket != -1 && lastBracket > firstBracket) {
        payload = payload.substring(firstBracket + 1, lastBracket);
        error = deserializeJson(busDoc, payload);
      }
    }

    if (!error) {
      JsonArray times = busDoc["Times"];
      if (times.isNull()) times = busDoc[0]["Times"];

      if (!times.isNull()) {
        String msg = "Next Shuttles In: ";
        int count = 0;
        for (JsonObject t : times) {
          if (!t.containsKey("Seconds") || t["Seconds"].isNull()) continue;
          int sec = t["Seconds"];
          if (sec <= 0) continue;
          int min = sec / 60;
          if (min < 1) min = 1;
          msg += String(min) + "m ";
          if (++count >= 3) break;
        }

        if (count == 0) {
          displayText = "No valid times";
          Serial.println("No valid bus times found");
        } else {
          displayText = msg;
          Serial.println("Shuttle times: " + displayText);
        }
      } else {
        displayText = "No times";
        Serial.println("No bus times found");
      }
    } else {
      displayText = "Bus parse error";
      Serial.print("Bus JSON error: ");
      Serial.println(error.c_str());
    }
  } else {
    displayText = "Bus HTTP " + String(httpCode);
    Serial.println(displayText);
  }

  http.end();
}

// --- Excuse ---
void fetchExcuse() {
  HTTPClient http;
  http.begin(excusesURL);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error && doc.containsKey("text")) {
      String excuse = doc["text"].as<String>();
      displayText = "Some dev said... " + excuse;
      Serial.println(displayText);
    } else {
      displayText = "Excuse parse error";
      Serial.println("Excuse JSON error");
    }
  } else {
    displayText = "Excuse HTTP " + String(httpCode);
    Serial.println(displayText);
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
