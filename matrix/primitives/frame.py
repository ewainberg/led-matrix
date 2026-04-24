from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from matrix.ctx import RGB, Viewport, RenderContext
from matrix.pipeline import Sample


@dataclass
class FramePrimitive:
    color: RGB
    thickness: int = 1  # keep 1 for 8px

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        if vp.w <= 1 or vp.h <= 1:
            return []

        x0, y0 = vp.x, vp.y
        x1, y1 = vp.x + vp.w - 1, vp.y + vp.h - 1

        out: list[Sample] = []
        i = 0

        for x in range(x0, x1 + 1):
            out.append(Sample(x=x, y=y0, color=self.color, meta_i=i)); i += 1
        for y in range(y0 + 1, y1):
            out.append(Sample(x=x1, y=y, color=self.color, meta_i=i)); i += 1
        for x in range(x1, x0 - 1, -1):
            out.append(Sample(x=x, y=y1, color=self.color, meta_i=i)); i += 1
        for y in range(y1 - 1, y0, -1):
            out.append(Sample(x=x0, y=y, color=self.color, meta_i=i)); i += 1

        return out