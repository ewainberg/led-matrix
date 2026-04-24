from __future__ import annotations

from dataclasses import dataclass

from matrix.pipeline import Effect, Sample
from matrix.ctx import RenderContext, Viewport


@dataclass
class PhaseShiftWrap(Effect):
    axis: str  # "x" or "y"
    speed_px_s: float
    direction: int = 1  # 1 or -1

    def apply(self, s: Sample, ctx: RenderContext, vp: Viewport) -> Sample:
        d = int(ctx.t * self.speed_px_s) * self.direction
        if self.axis == "y":
            y = s.y - d
            if vp.h > 0:
                y = vp.y + ((y - vp.y) % vp.h)
            s.y = y
        else:
            x = s.x - d
            if vp.w > 0:
                x = vp.x + ((x - vp.x) % vp.w)
            s.x = x
        return s