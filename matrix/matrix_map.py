from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MatrixMap:
    w: int
    h: int
    column_major: bool = True
    zigzag: bool = True
    flip_x: bool = False
    flip_y: bool = False

    def xy_to_index(self, x: int, y: int) -> int:
        if self.flip_x:
            x = (self.w - 1) - x
        if self.flip_y:
            y = (self.h - 1) - y

        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return -1

        # Matches: NEO_MATRIX_TOP + NEO_MATRIX_LEFT + NEO_MATRIX_COLUMNS + NEO_MATRIX_ZIGZAG
        if self.column_major:
            if self.zigzag and (x % 2 == 1):
                y = (self.h - 1) - y
            return x * self.h + y

        # Row-major fallback (not your current wiring)
        if self.zigzag and (y % 2 == 1):
            x = (self.w - 1) - x
        return y * self.w + x
