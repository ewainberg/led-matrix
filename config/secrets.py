import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_KEY = os.getenv("WEATHER_KEY", "")
NEXT_URL = os.getenv("NEXT_URL", "")

if not WEATHER_KEY:
    raise RuntimeError("WEATHER_KEY missing in .env")
