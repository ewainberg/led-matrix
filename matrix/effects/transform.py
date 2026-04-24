from __future__ import annotations

import math
from dataclasses import dataclass

from matrix.pipeline import Effect, Sample
from matrix.ctx import RenderContext, Viewport


@dataclass
class Bounce(Effect):
    axis: str  # "x" or "y"
    amplitude_px: int = 1
    period_s: float = 0.6

    def apply(self, s: Sample, ctx: RenderContext, vp: Viewport) -> Sample:
        if self.period_s <= 0:
            return s
        phase = (ctx.t / self.period_s) * (2 * math.pi)
        off = int(round(math.sin(phase) * self.amplitude_px))
        if self.axis == "x":
            s.x += off
        else:
            s.y += off
        return s


@dataclass
class Wave(Effect):
    axis: str = "y"
    amplitude_px: int = 1
    period_px: int = 16
    speed_px_s: float = 10.0

    def apply(self, s: Sample, ctx: RenderContext, vp: Viewport) -> Sample:
        if self.period_px <= 0:
            return s
        phase = (s.x + int(ctx.t * self.speed_px_s)) / self.period_px * (2 * math.pi)
        off = int(round(math.sin(phase) * self.amplitude_px))
        if self.axis == "y":
            s.y += off
        else:
            s.x += off
        return s