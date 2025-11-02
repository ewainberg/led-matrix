#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include <time.h>
#include "config.h"

// ---------- MATRIX SETUP ----------
#define PIN 23
#define MATRIX_WIDTH 160
#define MATRIX_HEIGHT 8
#define TEXT_AREA_WIDTH 128
#define CLOCK_X_START 128

Adafruit_NeoMatrix matrix(
  MATRIX_WIDTH, MATRIX_HEIGHT, PIN,
  NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG,
  NEO_GRB + NEO_KHZ800
);

// ---------- TEXT CANVAS ----------
GFXcanvas1 textCanvas(TEXT_AREA_WIDTH, MATRIX_HEIGHT);

// ---------- TIMING ----------
const unsigned long dataInterval = 60000;
unsigned long lastDataFetch   = 0;
unsigned long lastModeSwitch  = 0;
unsigned long currentModeDuration = 0;

// Explicit per-mode durations (milliseconds)
const uint32_t DURATION_WEATHER       = 9000;
const uint32_t DURATION_BUS           = 9000;
const uint32_t DURATION_EXCUSE        = 20000;
const uint32_t DURATION_MESSAGE_SHOW  = 20000; // one clean pass
const uint32_t DURATION_MESSAGE_EMPTY = 250;  // bounce out fast

// Precise scroll control (slightly faster)
const uint16_t SCROLL_DELAY_MS        = 40; // frame delay
const uint8_t  SCROLL_PIXELS_PER_STEP = 3;  // px per frame

// New: pause before scrolling starts
const uint16_t SCROLL_START_PAUSE_MS  = 3000; // 1.5s pause at x=0

// ---------- MODES ----------
enum DisplayMode {
  MODE_WEATHER,
  MODE_BUS,
  MODE_EXCUSE,
  MODE_MESSAGE,
  MODE_COUNT
};
DisplayMode currentMode = MODE_WEATHER;

// ---------- STATE ----------
String displayText = "";
String timeText    = "";
int16_t scrollX    = 0;      // start at left now
int     scrollPasses = 0;

// New: scrolling pause state
bool scrollPaused = true;
unsigned long scrollPauseStart = 0;

// ---------- COLORS ----------
uint16_t weatherColor;
uint16_t timeColor;
uint16_t busColor;
uint16_t excuseColor;
uint16_t messageColor;

// ---------- DECLARATIONS ----------
void fetchWeather();
void fetchBusTimes();
void fetchExcuse();
bool handleMessageMode(); // returns true if a message will be displayed

void updateClock();
void updateDisplay();
void scrollText();
void drawClock();

uint32_t getModeDuration(DisplayMode m);
uint16_t getModeColor(DisplayMode mode);
int16_t textWidth(const String &s);
String sanitizeOneLine(const String &in);

// ---------- HELPERS ----------
String sanitizeOneLine(const String &in) {
  String s = in;
  s.replace("\r", " ");
  s.replace("\n", " ");
  s.replace("\t", " ");
  s.trim();
  return s;
}

int16_t textWidth(const String &s) {
  textCanvas.setTextWrap(false);
  textCanvas.setTextSize(1);
  textCanvas.setTextColor(1);
  int16_t x1, y1; uint16_t w, h;
  textCanvas.getTextBounds(s, 0, 0, &x1, &y1, &w, &h);
  return (int16_t)w;
}

uint16_t getModeColor(DisplayMode mode) {
  switch (mode) {
    case MODE_WEATHER: return weatherColor;
    case MODE_BUS:     return busColor;
    case MODE_EXCUSE:  return excuseColor;
    case MODE_MESSAGE: return messageColor;
    default:           return matrix.Color(255, 255, 255);
  }
}

uint32_t getModeDuration(DisplayMode m) {
  switch (m) {
    case MODE_WEATHER: return DURATION_WEATHER;
    case MODE_BUS:     return DURATION_BUS;
    case MODE_EXCUSE:  return DURATION_EXCUSE;
    case MODE_MESSAGE: default: return 4000;
  }
}

// ---------- CLOCK ----------
void updateClock() {
  struct tm timeinfo;
  if (getLocalTime(&timeinfo)) {
    char buf[8];
    strftime(buf, sizeof(buf), "%I:%M", &timeinfo); // 12h, no AM/PM
    String t = buf;
    if (t[0] == '0') t = t.substring(1);
    timeText = t;
  }
}

void drawClock() {
  matrix.setTextSize(1);
  matrix.setTextWrap(false);
  matrix.setTextColor(timeColor);

  int16_t wClock = textWidth(timeText);
  int16_t xClock = (int16_t)MATRIX_WIDTH - wClock;
  if (xClock < CLOCK_X_START) xClock = CLOCK_X_START;

  matrix.fillRect(CLOCK_X_START, 0, MATRIX_WIDTH - CLOCK_X_START, MATRIX_HEIGHT, 0);
  matrix.setCursor(xClock, 0);
  matrix.print(timeText);
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, password);
  int retryCount = 0;
  while (WiFi.status() != WL_CONNECTED && retryCount < 20) {
    delay(500);
    Serial.print(".");
    retryCount++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected!");
    Serial.print("IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed!");
  }

  configTzTime("EST5EDT,M3.2.0,M11.1.0", "pool.ntp.org", "time.nist.gov");

  matrix.begin();
  matrix.setTextWrap(false);
  matrix.setBrightness(20);

  textCanvas.setTextWrap(false);
  textCanvas.setTextSize(1);
  textCanvas.setTextColor(1);

  weatherColor = matrix.Color(0, 150, 255);
  timeColor    = matrix.Color(0, 255, 100);
  busColor     = matrix.Color(255, 180, 0);
  excuseColor  = matrix.Color(255, 100, 255);
  messageColor = matrix.Color(255, 255, 0);

  fetchWeather();
  updateDisplay();
  scrollX = 0;
  scrollPaused = true;
  scrollPauseStart = millis();

  lastDataFetch = millis();
  lastModeSwitch = millis();
  currentModeDuration = getModeDuration(currentMode);
}

// ---------- LOOP ----------
void loop() {
  unsigned long now = millis();

  if (now - lastModeSwitch >= currentModeDuration) {
    currentMode = (DisplayMode)((currentMode + 1) % MODE_COUNT);
    updateDisplay();
    scrollX = 0;                 // start at left each mode
    scrollPaused = true;         // arm pause each mode
    scrollPauseStart = now;
    scrollPasses = 0;
    lastModeSwitch = now;
  }

  if (now - lastDataFetch >= dataInterval) {
    fetchWeather();
    fetchBusTimes();
    fetchExcuse();
    lastDataFetch = now;
  }

  updateClock();
  scrollText();
  delay(SCROLL_DELAY_MS);
}

// ---------- MODE / DISPLAY ----------
void updateDisplay() {
  Serial.println();
  switch (currentMode) {
    case MODE_WEATHER:
      Serial.println("Mode: Weather");
      fetchWeather();
      currentModeDuration = getModeDuration(MODE_WEATHER);
      break;

    case MODE_BUS:
      Serial.println("Mode: Bus");
      fetchBusTimes();
      currentModeDuration = getModeDuration(MODE_BUS);
      break;

    case MODE_EXCUSE:
      Serial.println("Mode: Excuse");
      fetchExcuse();
      currentModeDuration = getModeDuration(MODE_EXCUSE);
      break;

    case MODE_MESSAGE: {
      Serial.println("Mode: Message");
      bool willDisplay = handleMessageMode();
      currentModeDuration = willDisplay ? DURATION_MESSAGE_SHOW : DURATION_MESSAGE_EMPTY;
      break;
    }
  }

  Serial.println("[Display] " + displayText);

  // Reset scrolling state for this mode: start at left and pause
  scrollX = 0;
  scrollPaused = true;
  scrollPauseStart = millis();
  scrollPasses = 0;
}

// ---------- FETCH FUNCTIONS ----------
void fetchWeather() {
  HTTPClient http;
  http.begin(weatherPath);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<2048> doc;
    if (!deserializeJson(doc, payload)) {
      String tempF = doc["current"]["temp_f"].as<String>();
      String condition = doc["current"]["condition"]["text"].as<String>();
      displayText = sanitizeOneLine(condition + ", " + tempF + "F");
    } else {
      displayText = "Weather parse error";
    }
  } else {
    displayText = "Weather HTTP " + String(httpCode);
  }
  http.end();
}

void fetchBusTimes() {
  HTTPClient http;
  http.begin(busURL);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    payload.trim();
    DynamicJsonDocument doc(8192);
    if (!deserializeJson(doc, payload)) {
      JsonArray times = doc["Times"];
      if (times.isNull() && doc.is<JsonArray>()) times = doc[0]["Times"];
      if (!times.isNull()) {
        String msg = "Bus: ";
        int count = 0;
        for (JsonObject t : times) {
          int sec = t["Seconds"] | -1;
          if (sec > 0) {
            int min = (sec / 60);
            if (min < 1) min = 1;
            msg += String(min) + "m ";
            if (++count >= 3) break;
          }
        }
        displayText = count ? sanitizeOneLine(msg) : "Bus times unavailable";
      } else displayText = "No times";
    } else displayText = "Bus parse error";
  } else displayText = "Bus HTTP " + String(httpCode);
  http.end();
}

void fetchExcuse() {
  HTTPClient http;
  http.begin(excusesURL);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<1024> doc;
    if (!deserializeJson(doc, payload) && doc.containsKey("text")) {
      displayText = sanitizeOneLine("Excuse: " + doc["text"].as<String>());
    } else displayText = "Excuse parse error";
  } else displayText = "Excuse HTTP " + String(httpCode);

  http.end();
}

// ---------- MESSAGE MODE (your exact flow) ----------
bool handleMessageMode() {
  // 1) GET current message.txt
  HTTPClient http;
  http.begin(messageURL); // messageURL must include ?key=... in config.h
  int httpCode = http.GET();

  if (httpCode != 200) {
    http.end();
    displayText = "";        // nothing to show
    Serial.printf("[Message] CURRENT HTTP %d\n", httpCode);
    return false;            // exit mode quickly
  }

  String msg = http.getString();
  http.end();
  msg.trim();

  if (msg.length() == 0 || msg == "No messages" || msg == "No Messages") {
    // 2) If "No Messages" -> call nextURL and EXIT mode
    HTTPClient http2;
    http2.begin(nextURL);    // nextURL must include ?key=...
    int code2 = http2.GET();
    http2.end();
    Serial.printf("[Message] NONE. NEXT HTTP %d\n", code2);
    displayText = "";        // nothing to display this cycle
    return false;            // exit mode quickly
  }

  // 3) If there IS a message -> set displayText, then call nextURL BEFORE scrolling, then display once and exit
  displayText = sanitizeOneLine(msg);
  Serial.printf("[Message] SHOW: %s\n", displayText.c_str());

  // pop immediately so next time messageURL returns the next one
  HTTPClient http3;
  http3.begin(nextURL);
  int code3 = http3.GET();
  http3.end();
  Serial.printf("[Message] NEXT pop HTTP %d\n", code3);

  // will display this cycle
  return true;
}

// ---------- RENDER / SCROLL ----------
void scrollText() {
  matrix.fillRect(0, 0, TEXT_AREA_WIDTH, MATRIX_HEIGHT, 0);
  textCanvas.fillScreen(0);
  textCanvas.setTextWrap(false);
  textCanvas.setTextSize(1);
  textCanvas.setTextColor(1);

  int16_t w = textWidth(displayText);

  // force scrolling in EXCUSE and MESSAGE; otherwise only if too wide
  bool forceScroll  = (currentMode == MODE_EXCUSE || currentMode == MODE_MESSAGE);
  bool needsScroll  = forceScroll || (w > TEXT_AREA_WIDTH);

  if (!needsScroll) {
    // Static text
    textCanvas.setCursor(0, 0);
    textCanvas.print(displayText);
  } else {
    // Pause at left before scrolling
    if (scrollPaused) {
      if (millis() - scrollPauseStart >= SCROLL_START_PAUSE_MS) {
        scrollPaused = false; // start moving
      }
    }

    // Draw at current position (starts at x=0)
    textCanvas.setCursor(scrollX, 0);
    textCanvas.print(displayText);

    // Move only after pause ends
    if (!scrollPaused) {
      scrollX -= SCROLL_PIXELS_PER_STEP;
    }

    // One pass ends when right edge clears the left edge
    if (scrollX + w < 0) {
      // Do not wrap within the same mode; leave it off-screen until mode timer flips
      // If you prefer wrap, uncomment below:
      scrollX = 0; scrollPaused = true; scrollPauseStart = millis();
      scrollPasses++;
    }
  }

  matrix.drawBitmap(0, 0, textCanvas.getBuffer(),
                    TEXT_AREA_WIDTH, MATRIX_HEIGHT,
                    getModeColor(currentMode), 0);

  drawClock();
  matrix.show();
}
