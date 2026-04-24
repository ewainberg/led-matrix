"""
Two-player horizontal Tetris game logic.

Layout on the 160×8 matrix:
  cols  0–77   Player 1 playfield  (pieces enter from col 0, travel right)
  cols 78–79   Player 1 floor wall
  cols 80–81   Player 2 floor wall
  cols 82–159  Player 2 playfield  (pieces enter from col 159, travel left)

Each playfield is FIELD_W × FIELD_H (78 × 8).
Pieces are represented in (row, col_offset) notation where col_offset=0 is
the leading edge of the piece (the edge closest to the floor wall).

A "line clear" happens when an entire row-column (all 8 rows at a single
column index) is filled — i.e. a full vertical slice of the playfield.
"""
from __future__ import annotations

import time
import threading
from copy import deepcopy
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIELD_W = 78   # columns in each playfield
FIELD_H = 8    # rows (= matrix height)

# Gravity: seconds between automatic piece advances (one column step)
BASE_TICK_S = 0.2
MIN_TICK_S  = 0.05
SPEED_UP_PER_LINE = 0.01   # seconds shaved off per line cleared

# Player colours (RGB)
P1_COLOR: tuple[int, int, int] = (0, 220, 255)    # cyan
P2_COLOR: tuple[int, int, int] = (255, 140, 0)    # orange
FLOOR_COLOR: tuple[int, int, int] = (255, 255, 255)

# ---------------------------------------------------------------------------
# Piece definitions
# Pieces are stored in "horizontal" orientation: pieces travel along the
# x-axis (columns) so the piece's *depth* (in the travel direction) is the
# column span and its *width* is the row span.
#
# Each shape is a list of (row, col_offset) pairs relative to the piece's
# anchor.  col_offset=0 is the leading edge (side closest to the floor wall).
# Rows are 0-indexed from the top of the 8-row field.
# ---------------------------------------------------------------------------

PIECES: list[list[list[tuple[int, int]]]] = [
    # I  —  1×4 bar
    [
        [(0,0),(1,0),(2,0),(3,0)],   # rotation 0  (vertical bar, 4 rows tall)
        [(0,0),(0,1),(0,2),(0,3)],   # rotation 1  (horizontal bar, 4 cols deep)
    ],
    # O  —  2×2 square (only one rotation)
    [
        [(0,0),(1,0),(0,1),(1,1)],
    ],
    # T
    [
        [(0,0),(1,0),(2,0),(1,1)],   # T pointing right
        [(0,0),(1,0),(0,1),(0,2)],
        [(0,1),(1,0),(1,1),(2,1)],
        [(0,0),(0,1),(0,2),(1,2)],   # unused but kept for symmetry
    ],
    # S
    [
        [(1,0),(2,0),(0,1),(1,1)],
        [(0,0),(0,1),(1,1),(1,2)],
    ],
    # Z
    [
        [(0,0),(1,0),(1,1),(2,1)],
        [(1,0),(0,1),(1,1),(0,2)],
    ],
    # L
    [
        [(0,0),(1,0),(2,0),(2,1)],
        [(0,0),(0,1),(0,2),(1,0)],
        [(0,0),(0,1),(1,1),(2,1)],
        [(2,0),(0,1),(1,1),(2,1)],
    ],
    # J
    [
        [(0,0),(1,0),(2,0),(0,1)],
        [(0,0),(1,0),(1,1),(1,2)],
        [(2,0),(0,1),(1,1),(2,1)],
        [(0,0),(0,1),(0,2),(1,2)],
    ],
]

PIECE_COLORS: list[tuple[int, int, int]] = [
    (0, 240, 240),   # I  — cyan
    (240, 240, 0),   # O  — yellow
    (160, 0, 240),   # T  — purple
    (0, 240, 0),     # S  — green
    (240, 0, 0),     # Z  — red
    (240, 160, 0),   # L  — orange
    (0, 0, 240),     # J  — blue
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

import random as _random

def _rand_piece_idx() -> int:
    return _random.randint(0, len(PIECES) - 1)


# ---------------------------------------------------------------------------
# TetrisPiece
# ---------------------------------------------------------------------------

class TetrisPiece:
    """A live (falling) piece."""

    def __init__(self, piece_idx: int, row: int, col: int, rotation: int = 0) -> None:
        self.piece_idx = piece_idx
        self.row = row          # top-left anchor row
        self.col = col          # leading-edge column
        self.rotation = rotation % len(PIECES[piece_idx])
        self.color: tuple[int, int, int] = PIECE_COLORS[piece_idx]

    def cells(self) -> list[tuple[int, int]]:
        """Return absolute (row, col) positions for every filled cell."""
        shape = PIECES[self.piece_idx][self.rotation]
        return [(self.row + dr, self.col + dc) for dr, dc in shape]

    def rotated(self, delta: int) -> "TetrisPiece":
        new_rot = (self.rotation + delta) % len(PIECES[self.piece_idx])
        return TetrisPiece(self.piece_idx, self.row, self.col, new_rot)

    def moved(self, drow: int = 0, dcol: int = 0) -> "TetrisPiece":
        return TetrisPiece(self.piece_idx, self.row + drow, self.col + dcol, self.rotation)

    def _bounding_col_max(self) -> int:
        return max(c for _, c in self.cells())

    def _bounding_row_min(self) -> int:
        return min(r for r, _ in self.cells())

    def _bounding_row_max(self) -> int:
        return max(r for r, _ in self.cells())


# ---------------------------------------------------------------------------
# TetrisBoard  (one player)
# ---------------------------------------------------------------------------

# Cell value: None = empty, tuple[int,int,int] = locked colour
GridCell = Optional[tuple[int, int, int]]


class TetrisBoard:
    """
    Single-player board.

    `direction` is either +1 (pieces travel toward higher col = P1)
                        or -1 (pieces travel toward lower col = P2).
    For P1: pieces spawn at col=0 and move toward col=FIELD_W-1 (floor at right).
    For P2: the same logical model applies; the scene builder mirrors it.
    """

    def __init__(self, player: int) -> None:
        self.player = player  # 1 or 2
        # grid[row][col] — None means empty
        self.grid: list[list[GridCell]] = [
            [None] * FIELD_W for _ in range(FIELD_H)
        ]
        self.score = 0
        self.lines_cleared = 0
        self.game_over = False
        self.active: Optional[TetrisPiece] = None
        self.next_piece_idx: int = _rand_piece_idx()
        self._spawn_piece()

    # ------------------------------------------------------------------
    # Spawn
    # ------------------------------------------------------------------

    def _spawn_piece(self) -> None:
        idx = self.next_piece_idx
        self.next_piece_idx = _rand_piece_idx()

        # Start in middle of field vertically, at leading edge (col=0)
        rot = 0
        shape = PIECES[idx][rot]
        row_span = max(r for r, _ in shape) - min(r for r, _ in shape) + 1
        start_row = max(0, (FIELD_H - row_span) // 2)

        piece = TetrisPiece(idx, start_row, 0, rot)

        # Check immediate collision (game over)
        if self._collides(piece):
            self.game_over = True
            self.active = None
        else:
            self.active = piece

    # ------------------------------------------------------------------
    # Collision
    # ------------------------------------------------------------------

    def _collides(self, piece: TetrisPiece) -> bool:
        for r, c in piece.cells():
            if r < 0 or r >= FIELD_H:
                return True
            if c < 0 or c >= FIELD_W:
                return True
            if self.grid[r][c] is not None:
                return True
        return False

    # ------------------------------------------------------------------
    # Gravity tick — advance piece one column toward the floor
    # ------------------------------------------------------------------

    def gravity_tick(self) -> None:
        if self.game_over or self.active is None:
            return

        advanced = self.active.moved(dcol=1)

        if self._collides(advanced):
            # Lock the current piece
            self._lock(self.active)
            cleared = self._clear_lines()
            self.lines_cleared += cleared
            self.score += [0, 1, 3, 6, 10][min(cleared, 4)]
            self._spawn_piece()
        else:
            self.active = advanced

    # ------------------------------------------------------------------
    # Lock
    # ------------------------------------------------------------------

    def _lock(self, piece: TetrisPiece) -> None:
        for r, c in piece.cells():
            if 0 <= r < FIELD_H and 0 <= c < FIELD_W:
                self.grid[r][c] = piece.color

    # ------------------------------------------------------------------
    # Line clear — a "line" here is a full *column* (all 8 rows filled)
    # ------------------------------------------------------------------

    def _clear_lines(self) -> int:
        cleared = 0
        new_cols: list[list[GridCell]] = []
        for c in range(FIELD_W):
            if all(self.grid[r][c] is not None for r in range(FIELD_H)):
                cleared += 1
                # Don't keep this column; it clears
            else:
                new_cols.append([self.grid[r][c] for r in range(FIELD_H)])

        if cleared == 0:
            return 0

        # Rebuild grid: cleared columns are removed (field shrinks toward floor),
        # new empty columns inserted at spawn side (col 0).
        empty_col: list[GridCell] = [None] * FIELD_H
        while len(new_cols) < FIELD_W:
            new_cols.insert(0, list(empty_col))

        for r in range(FIELD_H):
            for c in range(FIELD_W):
                self.grid[r][c] = new_cols[c][r]

        return cleared

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def move_up(self) -> None:
        if self.active is None or self.game_over:
            return
        moved = self.active.moved(drow=-1)
        if not self._collides(moved):
            self.active = moved

    def move_down(self) -> None:
        if self.active is None or self.game_over:
            return
        moved = self.active.moved(drow=1)
        if not self._collides(moved):
            self.active = moved

    def rotate_cw(self) -> None:
        if self.active is None or self.game_over:
            return
        rotated = self.active.rotated(1)
        if not self._collides(rotated):
            self.active = rotated
        else:
            # Wall kick: try nudging up or down by 1
            for nudge in (-1, 1, -2, 2):
                nudged = rotated.moved(drow=nudge)
                if not self._collides(nudged):
                    self.active = nudged
                    return

    def rotate_ccw(self) -> None:
        if self.active is None or self.game_over:
            return
        rotated = self.active.rotated(-1)
        if not self._collides(rotated):
            self.active = rotated
        else:
            for nudge in (-1, 1, -2, 2):
                nudged = rotated.moved(drow=nudge)
                if not self._collides(nudged):
                    self.active = nudged
                    return


# ---------------------------------------------------------------------------
# TetrisGame  (two boards, shared tick rate, thread-safe action queue)
# ---------------------------------------------------------------------------

class TetrisGame:
    def __init__(self) -> None:
        self.board1 = TetrisBoard(player=1)
        self.board2 = TetrisBoard(player=2)
        self._lock = threading.Lock()
        self._last_tick_at: float = time.time()
        self._tick_interval: float = BASE_TICK_S
        self.started_at: float = time.time()

    # ------------------------------------------------------------------
    # Called by the background loop at ~4 Hz (every 0.25 s)
    # ------------------------------------------------------------------

    def tick(self) -> None:
        now = time.time()
        with self._lock:
            if now - self._last_tick_at >= self._tick_interval:
                self._last_tick_at = now
                if not self.board1.game_over:
                    self.board1.gravity_tick()
                if not self.board2.game_over:
                    self.board2.gravity_tick()

                # Speed up based on total lines cleared
                total_lines = self.board1.lines_cleared + self.board2.lines_cleared
                self._tick_interval = max(
                    MIN_TICK_S,
                    BASE_TICK_S - total_lines * SPEED_UP_PER_LINE,
                )

    # ------------------------------------------------------------------
    # Player actions (thread-safe)
    # ------------------------------------------------------------------

    def action(self, player: int, act: str) -> None:
        board = self.board1 if player == 1 else self.board2
        with self._lock:
            if act == "up":
                board.move_up()
            elif act == "down":
                board.move_down()
            elif act == "rotate_cw":
                board.rotate_cw()
            elif act == "rotate_ccw":
                board.rotate_ccw()

    # ------------------------------------------------------------------
    # Snapshot for rendering (returns copies so renderer is lock-free)
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "board1_grid": deepcopy(self.board1.grid),
                "board1_active": deepcopy(self.board1.active),
                "board1_score": self.board1.score,
                "board1_lines": self.board1.lines_cleared,
                "board1_over": self.board1.game_over,
                "board2_grid": deepcopy(self.board2.grid),
                "board2_active": deepcopy(self.board2.active),
                "board2_score": self.board2.score,
                "board2_lines": self.board2.lines_cleared,
                "board2_over": self.board2.game_over,
                "tick_interval": self._tick_interval,
            }

    @property
    def both_game_over(self) -> bool:
        with self._lock:
            return self.board1.game_over and self.board2.game_over
