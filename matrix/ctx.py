from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from PIL import Image, ImageDraw

RGB = Tuple[int, int, int]


@dataclass(frozen=True)
class Viewport:
    x: int
    y: int
    w: int
    h: int

    def inset(self, n: int) -> "Viewport":
        return Viewport(
            self.x + n,
            self.y + n,
            max(0, self.w - 2 * n),
            max(0, self.h - 2 * n),
        )

    def contains(self, x: int, y: int) -> bool:
        return (self.x <= x < self.x + self.w) and (self.y <= y < self.y + self.h)


@dataclass
class RenderContext:
    img: Image.Image
    draw: ImageDraw.ImageDraw
    t: float
    screen_w: int
    screen_h: int

    def putpixel(self, x: int, y: int, color: RGB) -> None:
        if 0 <= x < self.screen_w and 0 <= y < self.screen_h:
            self.img.putpixel((x, y), color)