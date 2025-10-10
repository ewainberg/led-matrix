#include <WiFiEnterprise.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include "config.h"  // contains: const char* username; const char* password;

// --- MATRIX SETUP ---
#define PIN 23
#define MATRIX_WIDTH 32
#define MATRIX_HEIGHT 8

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(
  MATRIX_WIDTH, MATRIX_HEIGHT, PIN,
  NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG,
  NEO_GRB + NEO_KHZ800
);

// --- WIFI ---
const char* ssid = "UCF_WPA2";

// --- WEATHER API ---
const String weatherURL = "http://api.weatherapi.com/v1";
const String weatherKey = "key=056112fc6a604f4aa5d190625250910";
const String weatherLocation = "q=Orlando";
const String orlandoWeatherPath = weatherURL + "/current.json?" + weatherKey + "&" + weatherLocation;

// --- BUS API ---
const String busURL = "https://ucf.transloc.com/Services/JSONPRelay.svc/GetStopArrivalTimes?apiKey=&stopIds=60&version=2";

// --- TIMING ---
const unsigned long dataInterval = 60000;
const unsigned long modeInterval = 10000;
unsigned long lastDataFetch = 0;
unsigned long lastModeSwitch = 0;

// --- MODES ---
enum DisplayMode {
  MODE_WEATHER,
  MODE_BUS,
  MODE_COUNT
};
DisplayMode currentMode = MODE_WEATHER;

// --- VARIABLES ---
String displayText = "";
int16_t scrollX = 0;

// --- FUNCTION DECLARATIONS ---
void fetchWeather();
void fetchBusTimes();
void updateDisplay();
void scrollText();

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

  // Initialize LED matrix
  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setBrightness(40);
  matrix.setTextColor(matrix.Color(0, 150, 255));

  // Fetch initial data
  fetchWeather();
  updateDisplay();
  scrollX = matrix.width();
  lastDataFetch = millis();
  lastModeSwitch = millis();
}

void loop() {
  unsigned long now = millis();

  if (now - lastModeSwitch >= modeInterval) {
    currentMode = (DisplayMode)((currentMode + 1) % MODE_COUNT);
    updateDisplay();
    lastModeSwitch = now;
  }

  if (now - lastDataFetch >= dataInterval) {
    if (currentMode == MODE_WEATHER) fetchWeather();
    else if (currentMode == MODE_BUS) fetchBusTimes();
    lastDataFetch = now;
  }

  scrollText();
  delay(75);
}

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
  }
  Serial.println("[Display] " + displayText);
  scrollX = matrix.width();
}

void fetchWeather() {
  HTTPClient http;
  http.begin(orlandoWeatherPath);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    StaticJsonDocument<1024> doc;
    deserializeJson(doc, payload);
    String tempF = doc["current"]["temp_f"].as<String>();
    displayText = "Orlando " + tempF + "F";
    Serial.println("Weather: " + displayText);
  } else {
    displayText = "Weather HTTP " + String(httpCode);
    Serial.println(displayText);
  }

  http.end();
}

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
        String msg = "Bus ";
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
          Serial.println("Bus times: " + displayText);
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
