from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from matrix.ctx import RGB, Viewport, RenderContext
from matrix.pipeline import Sample


@dataclass
class VerticalSpriteScroller:
    pixels: list[list[Optional[RGB]]]  # tall sprite
    colorize_none: Optional[RGB] = None
    speed_px_s: float = 6.0
    pause_s: float = 1.0
    loop: str = "wrap"  # wrap/pingpong

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        src_h = len(self.pixels)
        src_w = len(self.pixels[0]) if src_h else 0
        if src_h <= 0 or src_w <= 0 or vp.w <= 0 or vp.h <= 0:
            return []

        travel = max(0, src_h - vp.h)
        if travel == 0:
            offset = 0
        else:
            t = max(0.0, ctx.t - self.pause_s)
            raw = int(t * self.speed_px_s)
            if self.loop == "pingpong":
                period = travel * 2
                k = raw % max(1, period)
                offset = k if k <= travel else (period - k)
            else:
                offset = raw % (travel + 1)

        out: list[Sample] = []
        for yy in range(vp.h):
            sy = yy + offset
            if sy < 0 or sy >= src_h:
                continue
            row = self.pixels[sy]
            for xx in range(min(vp.w, src_w)):
                c = row[xx]
                if c is None:
                    continue
                out.append(Sample(x=vp.x + xx, y=vp.y + yy, color=c))
        return out