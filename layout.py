from __future__ import annotations

import math
from dataclasses import dataclass

from config import (
    TEXT_AREA_WIDTH_PX,
    SCROLL_START_PAUSE_S,
    SCROLL_GAP_PX,
    SCROLL_SPEED_PX_S,
    SCROLL_PASSES_MIN,
)

CHAR_PX = 6  # placeholder for 5x7+spacing; can replace with real font metrics later


@dataclass(frozen=True)
class ScrollPlan:
    needs_scroll: bool
    text_width_px: int
    cycle_distance_px: int
    cycle_time_s: float
    total_time_s: float


def estimate_text_width_px(text: str) -> int:
    return max(0, len(text)) * CHAR_PX


def compute_scroll_plan(text: str) -> ScrollPlan:
    w = estimate_text_width_px(text)

    if w <= TEXT_AREA_WIDTH_PX:
        return ScrollPlan(False, w, 0, 0.0, 0.0)

    cycle_distance = w + SCROLL_GAP_PX
    cycle_time = cycle_distance / max(1e-6, SCROLL_SPEED_PX_S)
    total = SCROLL_START_PAUSE_S + (SCROLL_PASSES_MIN * cycle_time)

    return ScrollPlan(True, w, cycle_distance, cycle_time, total)


def compute_mode_duration_s(mode: str, display_text: str, base_s: int, empty_message_s: int) -> int:
    if mode == "message" and not display_text.strip():
        return int(empty_message_s)

    plan = compute_scroll_plan(display_text)
    if plan.needs_scroll:
        return int(math.ceil(max(base_s, plan.total_time_s)))

    return int(base_s)
