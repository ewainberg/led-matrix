from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from matrix.ctx import RGB, Viewport, RenderContext
from matrix.pipeline import Sample


ARROW_5 = {
    "up": [
        "  #  ",
        " ### ",
        "#####",
        "  #  ",
        "  #  ",
    ],
    "down": [
        "  #  ",
        "  #  ",
        "#####",
        " ### ",
        "  #  ",
    ],
    "left": [
        "  #  ",
        " ##  ",
        "#####",
        " ##  ",
        "  #  ",
    ],
    "right": [
        "  #  ",
        "  ## ",
        "#####",
        "  ## ",
        "  #  ",
    ],
}


@dataclass
class ArrowPrimitive:
    direction: str
    color: RGB
    x: int
    y: int

    # Visible window bounds (in viewport coordinates)
    top_y: int = 0        # top of visible region
    bottom_y: int = 8     # bottom of visible region (e.g. vp.h, or 6 if framed)

    speed_px_s: float = 6.0
    pause_s: float = 0.0
    started_at: float | None = None

    def _bottom_pixel_y(self, ctx: RenderContext, sprite_h: int) -> int:
        start = self.started_at if self.started_at is not None else 0.0
        t = max(0.0, (ctx.t - start) - self.pause_s)
        raw = int(t * self.speed_px_s)

        # Range for the sprite's bottom pixel:
        # - start completely below bottom edge so it scrolls in smoothly
        # - end when it's fully above the top edge so it disappears before wrap
        y_max = self.bottom_y + sprite_h
        y_min = self.top_y - 1

        if y_max < y_min:
            y_min, y_max = y_max, y_min

        span = (y_max - y_min) + 1
        return y_max - (raw % max(1, span))

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        pat = ARROW_5.get(self.direction, ARROW_5["right"])
        sprite_h = len(pat)

        bottom_y = self._bottom_pixel_y(ctx, sprite_h)
        top_left_y = bottom_y - (sprite_h - 1)

        base_x = vp.x + self.x
        base_y = vp.y + self.y + top_left_y

        out: list[Sample] = []
        for yy, row in enumerate(pat):
            for xx, ch in enumerate(row):
                if ch == "#":
                    out.append(Sample(base_x + xx, base_y + yy, self.color))
        return out