from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from matrix.ctx import RGB, Viewport, RenderContext
from matrix.pipeline import Sample


@dataclass
class SpritePrimitive:
    pixels: list[list[Optional[RGB]]]  # None = transparent
    x: int = 0
    y: int = 0

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        out: list[Sample] = []
        h = len(self.pixels)
        w = len(self.pixels[0]) if h else 0

        for yy in range(h):
            for xx in range(w):
                c = self.pixels[yy][xx]
                if c is None:
                    continue
                out.append(Sample(x=vp.x + self.x + xx, y=vp.y + self.y + yy, color=c))
        return out