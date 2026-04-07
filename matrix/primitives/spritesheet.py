from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from PIL import Image

from matrix.ctx import RGB, Viewport, RenderContext
from matrix.pipeline import Sample


@lru_cache(maxsize=64)
def _load_rgba(path: str) -> Image.Image:
    return Image.open(path).convert("RGBA")


@dataclass
class SpriteSheetPrimitive:
    path: str
    frame_width: int
    frame_height: int

    x: int = 0
    y: int = 0

    fps: float = 6.0
    loop: bool = True
    frame_index: int | None = None  # if set, forces one frame

    # Replace pure black pixels with this color.
    # If None, original sprite colors are used.
    black_replacement: RGB | None = None

    # Alpha threshold for visibility
    alpha_threshold: int = 1

    def _sheet(self) -> Image.Image:
        return _load_rgba(self.path)

    def _frame_count(self) -> int:
        sheet = self._sheet()
        if self.frame_width <= 0 or self.frame_height <= 0:
            return 0
        cols = sheet.width // self.frame_width
        rows = sheet.height // self.frame_height
        return cols * rows

    def _current_frame_index(self, ctx: RenderContext) -> int:
        count = self._frame_count()
        if count <= 0:
            return 0

        if self.frame_index is not None:
            return max(0, min(self.frame_index, count - 1))

        raw = int(ctx.t * self.fps)
        if self.loop:
            return raw % count
        return min(raw, count - 1)

    def _frame_image(self, idx: int) -> Image.Image:
        sheet = self._sheet()
        cols = max(1, sheet.width // self.frame_width)

        col = idx % cols
        row = idx // cols

        left = col * self.frame_width
        top = row * self.frame_height
        right = left + self.frame_width
        bottom = top + self.frame_height

        return sheet.crop((left, top, right, bottom))

    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]:
        count = self._frame_count()
        if count <= 0:
            return []

        idx = self._current_frame_index(ctx)
        frame = self._frame_image(idx)
        px = frame.load()

        out: list[Sample] = []
        ox = vp.x + self.x
        oy = vp.y + self.y

        for yy in range(frame.height):
            for xx in range(frame.width):
                r, g, b, a = px[xx, yy]
                if a < self.alpha_threshold:
                    continue

                color: RGB
                if self.black_replacement is not None and r == 0 and g == 0 and b == 0:
                    color = self.black_replacement
                else:
                    color = (r, g, b)

                out.append(Sample(x=ox + xx, y=oy + yy, color=color))

        return out