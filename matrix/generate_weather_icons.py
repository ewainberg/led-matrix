from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class WeatherIcon:
    pixels: list[list[int]]
    primary: RGB
    secondary: RGB


ICON_SUNNY = WeatherIcon(
    pixels=[
        [0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    ],
    primary=(255, 180, 0),
    secondary=(255, 220, 100),
)

ICON_RAIN = WeatherIcon(
    pixels=[
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
    ],
    primary=(255, 255, 255),
    secondary=(0, 120, 255),
)

ICON_LIGHTNING = WeatherIcon(
    pixels=[
        [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    primary=(255, 255, 0),
    secondary=(255, 200, 0),
)

ICON_CLOUDY = WeatherIcon(
    pixels=[
        [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ],
    primary=(255, 255, 255),
    secondary=(255, 255, 255),
)

ICON_FOG = WeatherIcon(
    pixels=[
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    ],
    primary=(180, 180, 180),
    secondary=(220, 220, 220),
)

WEATHER_ICONS: dict[str, WeatherIcon] = {
    "sunny": ICON_SUNNY,
    "rain": ICON_RAIN,
    "lightning": ICON_LIGHTNING,
    "cloudy": ICON_CLOUDY,
    "fog": ICON_FOG,
}


def save_icon_png(icon: WeatherIcon, path: str | Path, lit_style: str = "primary") -> None:
    h = len(icon.pixels)
    w = len(icon.pixels[0]) if h else 0

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()

    for y, row in enumerate(icon.pixels):
        for x, v in enumerate(row):
            if not v:
                continue

            if lit_style == "secondary":
                color = icon.secondary
            elif lit_style == "checker":
                color = icon.primary if (x + y) % 2 == 0 else icon.secondary
            else:
                color = icon.primary

            px[x, y] = (*color, 255)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def generate_weather_icon_pngs(
    out_dir: str | Path = "/home/maxpower/ledmatrix/assets/weather",
    lit_style: str = "primary",
) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for name, icon in WEATHER_ICONS.items():
        save_icon_png(icon, out_path / f"{name}.png", lit_style=lit_style)


if __name__ == "__main__":
    generate_weather_icon_pngs(lit_style="primary")
    print("Generated native-size weather icon PNGs.")