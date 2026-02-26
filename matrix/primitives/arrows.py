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
    direction: str  # up/down/left/right
    color: RGB
    x: int
    y: int

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        pat = ARROW_5.get(self.direction, ARROW_5["right"])
        out: list[Sample] = []
        for yy, row in enumerate(pat):
            for xx, ch in enumerate(row):
                if ch == "#":
                    out.append(Sample(vp.x + self.x + xx, vp.y + self.y + yy, self.color))
        return out