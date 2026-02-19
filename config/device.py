# -------- APIs --------
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"
WEATHER_LOCATION = "Orlando"

BUS_URL = "https://ucf.transloc.com/Services/JSONPRelay.svc/GetStopArrivalTimes?apiKey=&stopIds=60&version=2"
EXCUSES_URL = "https://excuses.onrender.com/excuse"
MESSAGE_URL = "https://example.com/matrix-message/message.txt"

# -------- Timezone --------
TZ = "America/New_York"

# -------- Fetch timing --------
FETCH_INTERVAL_S = 30

# -------- Matrix geometry --------
MATRIX_WIDTH_PX = 160
MATRIX_HEIGHT_PX = 8
CLOCK_START_X_PX = 128

# Derived geometry
TEXT_AREA_WIDTH_PX = CLOCK_START_X_PX

# -------- Quiet hours --------
OFF_START = "18:00"
ON_START = "8:55"

# -------- Scroll behavior --------
SCROLL_START_PAUSE_S = 1.0
SCROLL_GAP_PX = 12
SCROLL_SPEED_PX_S = 60.0
SCROLL_PASSES_MIN = 2

# -------- Base durations --------
BASE_MODE_DURATIONS_S = {
    "weather": 10,
    "bus": 10,
    "excuse": 10,
    "message": 10,
}

EMPTY_MESSAGE_DURATION_S = 0
