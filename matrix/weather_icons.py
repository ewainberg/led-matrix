from __future__ import annotations

from pathlib import Path

WEATHER_ICON_DIR = Path(__file__).resolve().parent.parent / "assets" / "weather"


def normalize_weather_condition(display_text: str) -> str:
    return (display_text or "").split(",", 1)[0].strip().lower()


SUNNY_CONDITIONS = {
    "sunny",
    "clear",
}

CLOUDY_CONDITIONS = {
    "partly cloudy",
    "cloudy",
    "overcast",
    "patchy snow possible",
    "blowing snow",
    "blizzard",
    "patchy light snow",
    "light snow",
    "patchy moderate snow",
    "moderate snow",
    "patchy heavy snow",
    "heavy snow",
    "light snow showers",
    "moderate or heavy snow showers",
}

FOG_CONDITIONS = {
    "mist",
    "fog",
    "freezing fog",
}

LIGHTNING_CONDITIONS = {
    "thundery outbreaks possible",
    "patchy light rain with thunder",
    "moderate or heavy rain with thunder",
    "patchy light snow with thunder",
    "moderate or heavy snow with thunder",
}

RAIN_CONDITIONS = {
    "patchy rain possible",
    "patchy sleet possible",
    "patchy freezing drizzle possible",
    "patchy light drizzle",
    "light drizzle",
    "freezing drizzle",
    "heavy freezing drizzle",
    "patchy light rain",
    "light rain",
    "moderate rain at times",
    "moderate rain",
    "heavy rain at times",
    "heavy rain",
    "light freezing rain",
    "moderate or heavy freezing rain",
    "light sleet",
    "moderate or heavy sleet",
    "ice pellets",
    "light rain shower",
    "moderate or heavy rain shower",
    "torrential rain shower",
    "light sleet showers",
    "moderate or heavy sleet showers",
    "light showers of ice pellets",
    "moderate or heavy showers of ice pellets",
}


def get_weather_icon_path(display_text: str) -> str | None:
    condition = normalize_weather_condition(display_text)

    if condition in LIGHTNING_CONDITIONS:
        icon_name = "lightning"
    elif condition in RAIN_CONDITIONS:
        icon_name = "rain"
    elif condition in FOG_CONDITIONS:
        icon_name = "fog"
    elif condition in CLOUDY_CONDITIONS:
        icon_name = "cloudy"
    elif condition in SUNNY_CONDITIONS:
        icon_name = "sunny"
    else:
        return None

    path = WEATHER_ICON_DIR / f"{icon_name}.png"
    return str(path) if path.exists() else None