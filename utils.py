import os
import time


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
