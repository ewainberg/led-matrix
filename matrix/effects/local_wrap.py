from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from matrix.ctx import RenderContext, Viewport
from matrix.pipeline import Sample


@dataclass
class LocalWrapShift:
    axis: str              # "x" or "y"
    w: int                 # local box width
    h: int                 # local box height
    speed_px_s: float
    direction: int = 1     # +1 or -1
    origin_x: int = 0      # local box origin (absolute coords)
    origin_y: int = 0

    def apply(self, ctx: RenderContext, vp: Viewport, samples: Iterable[Sample]) -> List[Sample]:
        if self.w <= 0 or self.h <= 0:
            return list(samples)

        dt = ctx.t
        shift = int(dt * self.speed_px_s) * (1 if self.direction >= 0 else -1)

        out: List[Sample] = []
        for s in samples:
            # Only affect samples inside the local box
            if not (self.origin_x <= s.x < self.origin_x + self.w and self.origin_y <= s.y < self.origin_y + self.h):
                out.append(s)
                continue

            if self.axis == "x":
                rel = (s.x - self.origin_x + shift) % self.w
                nx = self.origin_x + rel
                ny = s.y
            else:
                rel = (s.y - self.origin_y + shift) % self.h
                nx = s.x
                ny = self.origin_y + rel

            out.append(Sample(x=nx, y=ny, color=s.color))  # KEEP COLOR
        return out