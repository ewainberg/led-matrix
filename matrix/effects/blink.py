from __future__ import annotations

from dataclasses import dataclass

from matrix.pipeline import Effect, Sample
from matrix.ctx import RenderContext, Viewport


@dataclass
class Blink(Effect):
    period_s: float = 1.0
    duty_cycle: float = 0.65

    def apply(self, s: Sample, ctx: RenderContext, vp: Viewport) -> Sample:
        if self.period_s <= 0:
            return s
        phase = (ctx.t % self.period_s) / self.period_s
        if phase >= self.duty_cycle:
            s.on = False
        return s
