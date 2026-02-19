import os
from dotenv import load_dotenv

load_dotenv()

# -------- Weather --------
WEATHER_KEY = os.getenv("WEATHER_KEY", "")
WEATHER_BASE_URL = os.getenv("WEATHER_BASE_URL", "http://api.weatherapi.com/v1")
WEATHER_LOCATION = os.getenv("WEATHER_LOCATION", "Orlando")

WEATHER_URL = f"{WEATHER_BASE_URL}/current.json?key={WEATHER_KEY}&q={WEATHER_LOCATION}"

# -------- APIs --------
BUS_URL = os.getenv("BUS_URL", "")
EXCUSES_URL = os.getenv("EXCUSES_URL", "")
MESSAGE_URL = os.getenv("MESSAGE_URL", "")
NEXT_URL = os.getenv("NEXT_URL", "")

# -------- Timezone --------
TZ = os.getenv("TZ", "America/New_York")

# -------- Fetch timing --------
FETCH_INTERVAL_S = int(os.getenv("FETCH_INTERVAL_S", 30))

# -------- Display geometry --------
TEXT_AREA_WIDTH_PX = int(os.getenv("TEXT_AREA_WIDTH_PX", 128))
MATRIX_WIDTH_PX = int(os.getenv("MATRIX_WIDTH_PX", 160))
MATRIX_HEIGHT_PX = int(os.getenv("MATRIX_HEIGHT_PX", 8))
CLOCK_START_X_PX = int(os.getenv("CLOCK_START_X_PX", 128))

# -------- Scroll behavior --------
SCROLL_START_PAUSE_S = float(os.getenv("SCROLL_START_PAUSE_S", 1.0))
SCROLL_GAP_PX = int(os.getenv("SCROLL_GAP_PX", 12))
SCROLL_SPEED_PX_S = float(os.getenv("SCROLL_SPEED_PX_S", 60.0))
SCROLL_PASSES_MIN = int(os.getenv("SCROLL_PASSES_MIN", 2))

# -------- Base durations --------
BASE_MODE_DURATIONS_S = {
    "weather": 10,
    "bus": 10,
    "excuse": 10,
    "message": 10,
}

EMPTY_MESSAGE_DURATION_S = 0
