#include <WiFi.h>           // use simple WiFi for Wokwi / non-enterprise
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include <time.h>

// --- MATRIX SETUP ---
#define PIN 23
#define MATRIX_WIDTH 32
#define MATRIX_HEIGHT 8

Adafruit_NeoMatrix matrix = Adafruit_NeoMatrix(
  MATRIX_WIDTH, MATRIX_HEIGHT, PIN,
  NEO_MATRIX_BOTTOM + NEO_MATRIX_LEFT + NEO_MATRIX_ROWS + NEO_MATRIX_ZIGZAG,
  NEO_GRB + NEO_KHZ800
);

// --- WIFI ---
const char* ssid = "Wokwi-GUEST";
const char* password = "";

// --- WEATHER API ---
String weatherURL = "http://api.weatherapi.com/v1";
String weatherKey = "key=056112fc6a604f4aa5d190625250910";
String weatherLocation = "q=Orlando";
String orlandoWeatherPath = weatherURL + "/current.json?" + weatherKey + "&" + weatherLocation;

StaticJsonDocument<1024> doc;
String currentTempF = "";

const unsigned long weatherInterval = 60000; // fetch weather every 60s
const unsigned long modeInterval = 10000;    // switch display every 10s
const unsigned long scrollSpeed = 75;

unsigned long lastWeather = 0;
unsigned long lastScroll = 0;
unsigned long lastModeSwitch = 0;

int16_t scrollX;
String displayText;

// --- MODES ---
enum DisplayMode { MODE_WEATHER, MODE_TIME };
DisplayMode currentMode = MODE_WEATHER;

// --- FUNCTION DECLARATIONS ---
void fetchWeather();
void updateDisplayText();
void scrollText();
void showTime();

void setup() {
  Serial.begin(115200);
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  // Setup NTP
  configTime(-5 * 3600, 0, "pool.ntp.org"); // EST offset

  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setBrightness(40);
  matrix.setTextColor(matrix.Color(0, 150, 255));

  fetchWeather();
  updateDisplayText();
  lastWeather = millis();
  lastModeSwitch = millis();
}

void loop() {
  unsigned long now = millis();

  if (now - lastWeather >= weatherInterval) {
    fetchWeather();
    updateDisplayText();
    lastWeather = now;
  }

  if (now - lastModeSwitch >= modeInterval) {
    currentMode = (currentMode == MODE_WEATHER) ? MODE_TIME : MODE_WEATHER;
    updateDisplayText();
    lastModeSwitch = now;
  }

  if (now - lastScroll >= scrollSpeed) {
    scrollText();
    lastScroll = now;
  }
}

void fetchWeather() {
  HTTPClient http;
  http.begin(orlandoWeatherPath);
  int httpCode = http.GET();

  if (httpCode > 0) {
    String payload = http.getString();
    deserializeJson(doc, payload);
    currentTempF = doc["current"]["temp_f"].as<String>();
    Serial.println("Weather updated: " + currentTempF + "F");
  } else {
    Serial.println("HTTP error: " + String(httpCode));
  }

  http.end();
}

void updateDisplayText() {
  if (currentMode == MODE_WEATHER) {
    displayText = "Orlando " + currentTempF + "F ";
  } else {
    time_t now;
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo)) {
      displayText = "No time data ";
      return;
    }
    char buf[16];
    strftime(buf, sizeof(buf), "%I:%M %p", &timeinfo);
    displayText = String(buf);
  }
  scrollX = matrix.width();
  Serial.println("=== Mode: " + String(currentMode == MODE_WEATHER ? "Weather" : "Time") + " ===");
  Serial.println("[Display] " + displayText);
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
