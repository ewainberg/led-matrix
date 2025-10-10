#include <WiFiEnterprise.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include "config.h"  // your WPA2 username/password

// --- MATRIX SETUP ---
#define PIN 23                // GPIO pin connected to WS2812B DIN
#define MATRIX_WIDTH 32
#define MATRIX_HEIGHT 8

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(
  32, 8, 23,
  NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG,
  NEO_GRB + NEO_KHZ800
);


// --- WIFI ---
const char* ssid = "UCF_WPA2";

// --- WEATHER API ---
String weatherURL = "http://api.weatherapi.com/v1";
String weatherKey = "key=056112fc6a604f4aa5d190625250910";
String weatherLocation = "q=Orlando";
String orlandoWeatherPath = weatherURL + "/current.json?" + weatherKey + "&" + weatherLocation;

StaticJsonDocument<1024> doc;
String currentTempF = "";

const unsigned long interval = 60000;  // 1 minute
unsigned long lastRequest = 0;         // updated after each run
int16_t scrollX;
String displayText;

// --- FUNCTION DECLARATIONS ---
void fetchAndDisplay();
void scrollText();

void setup() {
  Serial.begin(115200);

  // --- Connect to WPA2 Enterprise ---
  Serial.println("Connecting to WPA2-Enterprise WiFi...");
  if (WiFiEnterprise.begin(ssid, username, password, true)) {
    Serial.println("Connected!");
    Serial.print("IP: ");
    Serial.println(WiFiEnterprise.localIP());
  } else {
    Serial.println("Connection failed!");
  }

  // --- Initialize LED Matrix ---
  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setBrightness(40);
  matrix.setTextColor(matrix.Color(0, 150, 255));

  // --- Run immediately once ---
  fetchAndDisplay();
  lastRequest = millis();  // start timing cadence
}

void loop() {
  // --- Interval check with rollover-safe steady cadence ---
  unsigned long now = millis();
  if ((unsigned long)(now - lastRequest) >= interval) {
    fetchAndDisplay();
    lastRequest += interval;  // steady interval, not drifted by runtime
    // optional resync if far behind
    if ((unsigned long)(millis() - lastRequest) >= interval)
      lastRequest = millis();
  }

  // --- Scroll continuously ---
  scrollText();
  delay(75);  // adjust scroll speed
}

// --- Fetch weather & update display text ---
void fetchAndDisplay() {
  HTTPClient http;
  http.begin(orlandoWeatherPath);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    deserializeJson(doc, payload);
    currentTempF = doc["current"]["temp_f"].as<String>();
    displayText = "Orlando " + currentTempF + "F ";
    Serial.println(displayText);
  } else {
    displayText = "HTTP " + String(httpCode) + " ";
    Serial.print("HTTP error: ");
    Serial.println(httpCode);
  }

  http.end();
  scrollX = matrix.width();  // reset scroll position
}

// --- Scroll the current text leftward ---
void scrollText() {
  matrix.fillScreen(0);
  matrix.setCursor(scrollX, 0);
  matrix.print(displayText);
  matrix.show();

  scrollX--;
  if (scrollX < -((int)displayText.length() * 6)) {
    scrollX = matrix.width();  // reset scroll
  }
}
