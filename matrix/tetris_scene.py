"""
Renders a TetrisGame snapshot directly onto the PIL image.

Physical layout on the 160×8 matrix:
  cols  0–77   Player 1 playfield
  cols 78–79   Player 1 floor wall  (2 px wide, solid)
  cols 80–81   Player 2 floor wall  (2 px wide, solid)
  cols 82–159  Player 2 playfield   (mirrored: col 82 = logical col 77, col 159 = logical col 0)

We bypass the DrawUnit pipeline entirely and write pixels directly into the
PIL image via ctx.putpixel, which keeps the code simple and fast.
"""
from __future__ import annotations

from typing import Optional
from matrix.ctx import RenderContext, RGB
from matrix.tetris import (
    TetrisGame,
    FIELD_W,
    FIELD_H,
    P1_COLOR,
    P2_COLOR,
    FLOOR_COLOR,
    PIECE_COLORS,
)

# Physical pixel offsets
P1_FIELD_START = 0       # col 0  — leftmost column of P1 playfield
P1_FLOOR_START = 78      # cols 78–79 — P1 floor wall
P2_FLOOR_START = 80      # cols 80–81 — P2 floor wall
P2_FIELD_START = 82      # col 82 — leftmost physical column of P2 playfield
                          # P2 logical col 0 maps to physical col 159 (rightmost)
                          # P2 logical col N maps to physical col (159 - N)

FLOOR_WIDTH = 2

# Dim colour for locked cells (slightly darker than active piece)
def _dim(c: RGB, factor: float = 0.65) -> RGB:
    return (int(c[0] * factor), int(c[1] * factor), int(c[2] * factor))

# Blinking game-over colour cycle period
_BLINK_PERIOD = 0.5


def _p1_physical(logical_col: int) -> int:
    """P1: logical col 0 = physical col 0 (spawn side = left)."""
    return P1_FIELD_START + logical_col


def _p2_physical(logical_col: int) -> int:
    """P2: logical col 0 = physical col 159 (spawn side = right), floor at left."""
    # logical col 0 → physical 159
    # logical col 77 → physical 82
    return 159 - logical_col


def render_tetris(game: TetrisGame, ctx: RenderContext) -> None:
    snap = game.snapshot()
    t = ctx.t

    # ------------------------------------------------------------------
    # Floor walls (always on)
    # ------------------------------------------------------------------
    for row in range(FIELD_H):
        for fc in range(FLOOR_WIDTH):
            ctx.putpixel(P1_FLOOR_START + fc, row, FLOOR_COLOR)
            ctx.putpixel(P2_FLOOR_START + fc, row, FLOOR_COLOR)

    # ------------------------------------------------------------------
    # Player 1 board
    # ------------------------------------------------------------------
    _render_board(
        ctx=ctx,
        grid=snap["board1_grid"],
        active=snap["board1_active"],
        score=snap["board1_score"],
        game_over=snap["board1_over"],
        player_color=P1_COLOR,
        phys_fn=_p1_physical,
        t=t,
    )

    # ------------------------------------------------------------------
    # Player 2 board
    # ------------------------------------------------------------------
    _render_board(
        ctx=ctx,
        grid=snap["board2_grid"],
        active=snap["board2_active"],
        score=snap["board2_score"],
        game_over=snap["board2_over"],
        player_color=P2_COLOR,
        phys_fn=_p2_physical,
        t=t,
    )


def _render_board(
    *,
    ctx: RenderContext,
    grid: list[list[Optional[RGB]]],
    active,
    score: int,
    game_over: bool,
    player_color: RGB,
    phys_fn,
    t: float,
) -> None:
    # Draw locked cells
    for row in range(FIELD_H):
        for col in range(FIELD_W):
            cell = grid[row][col]
            if cell is not None:
                px = phys_fn(col)
                if 0 <= px < 160:
                    ctx.putpixel(px, row, _dim(cell))

    # Draw active piece
    if active is not None:
        for row, col in active.cells():
            if 0 <= row < FIELD_H and 0 <= col < FIELD_W:
                px = phys_fn(col)
                if 0 <= px < 160:
                    ctx.putpixel(px, row, active.color)

    # Game-over overlay: blink the whole board red
    if game_over:
        blink_on = int(t / _BLINK_PERIOD) % 2 == 0
        if blink_on:
            for row in range(FIELD_H):
                for col in range(FIELD_W):
                    px = phys_fn(col)
                    if 0 <= px < 160:
                        ctx.putpixel(px, row, (180, 0, 0))
