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

def _parse_hhmm(s: str):
    s = (s or "").strip()
    hh, mm = s.split(":")
    return int(hh), int(mm) 

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