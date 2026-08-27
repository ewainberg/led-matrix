from __future__ import annotations

from typing import Tuple

try:
    from rpi_ws281x import PixelStrip, Color
except ImportError:
    class PixelStrip:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            pass

        def begin(self):
            pass

        def setPixelColor(self, *args, **kwargs):
            pass

        def show(self):
            pass

    def Color(r: int, g: int, b: int):  # type: ignore[no-redef]
        return (r, g, b)

from config import device
from matrix.matrix_map import MatrixMap


RGB = Tuple[int, int, int]


class MatrixOutput:
    def __init__(self, w: int, h: int) -> None:
        self.w = w
        self.h = h
        self.n = w * h

        self.map = MatrixMap(
            w=w,
            h=h,
            column_major=device.COLUMN_MAJOR,
            zigzag=device.ZIGZAG,
            flip_x=device.FLIP_X,
            flip_y=device.FLIP_Y,
        )

        self.strip = PixelStrip(
            self.n,
            device.LED_GPIO,
            device.LED_FREQ_HZ,
            device.LED_DMA,
            device.LED_INVERT,
            device.LED_BRIGHTNESS,
            device.LED_CHANNEL,
        )
        self.strip.begin()

    def show_frame(self, img_rgb) -> None:
        # img_rgb is a PIL.Image in RGB mode
        px = img_rgb.load()

        for y in range(self.h):
            for x in range(self.w):
                i = self.map.xy_to_index(x, y)
                if i < 0:
                    continue
                r, g, b = px[x, y]
                self.strip.setPixelColor(i, Color(r, g, b))

        self.strip.show()

    def blackout(self) -> None:
        for i in range(self.n):
            self.strip.setPixelColor(i, Color(0, 0, 0))
        self.strip.show()
