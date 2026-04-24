from __future__ import annotations

from dataclasses import dataclass

from matrix.pipeline import Effect, Sample
from matrix.ctx import RenderContext, Viewport


@dataclass
class Dash(Effect):
    dash_len: int = 2
    gap_len: int = 2
    speed_px_s: float = 0.0  # 0 => static dotted

    def apply(self, s: Sample, ctx: RenderContext, vp: Viewport) -> Sample:
        if self.dash_len <= 0:
            s.on = False
            return s
        period = self.dash_len + max(0, self.gap_len)
        if period <= 0:
            return s
        phase = int(ctx.t * self.speed_px_s) if self.speed_px_s else 0
        k = (s.meta_i + phase) % period
        s.on = (k < self.dash_len)
        return s