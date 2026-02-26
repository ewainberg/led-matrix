from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

from matrix.ctx import RGB, Viewport, RenderContext
from matrix.pipeline import Sample


def _bbox(font: ImageFont.FreeTypeFont, s: str) -> tuple[int, int, int, int]:
    if not s:
        return (0, 0, 0, 0)
    return font.getbbox(s)


def _size(font: ImageFont.FreeTypeFont, s: str) -> tuple[int, int]:
    l, t, r, b = _bbox(font, s)
    return (r - l, b - t)


@dataclass
class TextPrimitive:
    text: str
    font: ImageFont.FreeTypeFont
    color: RGB

    mode: str = "auto"  # auto/static/scroll
    x_align: str = "left"  # left/center/right
    y_align: str = "center"  # top/center/bottom

    scroll_started_at: float = 0.0
    start_pause_s: float = 1.0
    gap_px: int = 12
    speed_px_s: float = 60.0

    def _xy(self, vp: Viewport) -> tuple[int, int, int, int]:
        l, t, r, b = _bbox(self.font, self.text)
        w = r - l
        h = b - t

        if self.x_align == "right":
            x = (vp.x + vp.w - w) - l
        elif self.x_align == "center":
            x = (vp.x + (vp.w - w) // 2) - l
        else:
            x = vp.x - l

        if self.y_align == "top":
            y = vp.y - t
        elif self.y_align == "bottom":
            y = (vp.y + vp.h - h) - t
        else:
            y = (vp.y + (vp.h - h) // 2) - t

        return x, y, w, h

    def _raster(self, x: int, y: int) -> list[Sample]:
        if not self.text:
            return []

        w, h = _size(self.font, self.text)
        if w <= 0 or h <= 0:
            return []

        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.text((0, 0), self.text, font=self.font, fill=1)

        out: list[Sample] = []
        px = mask.load()
        for yy in range(h):
            for xx in range(w):
                if px[xx, yy]:
                    out.append(Sample(x=x + xx, y=y + yy, color=self.color))
        return out

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        if not self.text or vp.w <= 0 or vp.h <= 0:
            return []

        x, y, w_text, _ = self._xy(vp)

        wants_scroll = (self.mode == "scroll") or (self.mode == "auto" and w_text > vp.w)
        if not wants_scroll:
            return self._raster(x, y)

        pause = self.start_pause_s
        dt = max(0.0, ctx.t - self.scroll_started_at - pause)
        cycle = w_text + self.gap_px
        if cycle <= 0:
            return self._raster(x, y)

        x0 = x + int(-((dt * self.speed_px_s) % cycle))
        s1 = self._raster(x0, y)
        s2 = self._raster(x0 + cycle, y)
        return s1 + s2