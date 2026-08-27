from __future__ import annotations

import os
import time
from datetime import datetime


def set_tz(tz: str) -> None:
    os.environ["TZ"] = tz
    try:
        time.tzset()
    except Exception:
        pass


def sanitize_one_line(s: str) -> str:
    return " ".join(
        s.replace("\r", " ").replace("\n", " ").replace("\t", " ").split()
    ).strip()


def clock_text() -> str:
    t = time.strftime("%I:%M")
    return t[1:] if t.startswith("0") else t

def _parse_hhmm(s: str) -> tuple[int, int]:
    s = (s or "").strip()
    try:
        hh, mm = s.split(":")
        return int(hh), int(mm)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid HH:MM time string: {s!r}") from exc

def is_quiet_hours(off_start: str, on_start: str, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    h1, m1 = _parse_hhmm(off_start)
    h2, m2 = _parse_hhmm(on_start)

    off = h1 * 60 + m1
    on = h2 * 60 + m2
    t = now.hour * 60 + now.minute

    if off == on:
        return True

    if off < on:
        return off <= t < on

    return (t >= off) or (t < on)


def is_time_reminder_active(
    day_of_week: int = 3,
    interval_m: int = 5,
    duration_s: int = 12,
    now: datetime | None = None,
) -> bool:
    now = now or datetime.now()
    if now.weekday() != day_of_week:
        return False
    if interval_m <= 0 or duration_s <= 0:
        return False
    return (now.minute % interval_m == 0) and (now.second < duration_s)