from __future__ import annotations

import time
import threading
from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class ModeSnapshot:
    ok: bool
    display_text: str
    raw: Optional[Any]
    error: Optional[str]
    fetched_at_unix: float


@dataclass
class State:
    time_text: str
    current_mode: str
    current_mode_duration_s: int
    weather: ModeSnapshot
    bus: ModeSnapshot
    excuse: ModeSnapshot
    message: ModeSnapshot


def snap_ok(display_text: str, raw: Any) -> ModeSnapshot:
    return ModeSnapshot(
        ok=True,
        display_text=display_text,
        raw=raw,
        error=None,
        fetched_at_unix=time.time(),
    )


def snap_err(msg: str) -> ModeSnapshot:
    return ModeSnapshot(
        ok=False,
        display_text=msg,
        raw=None,
        error=msg,
        fetched_at_unix=time.time(),
    )


class StateStore:
    def __init__(self, initial_time_text: str) -> None:
        now = time.time()
        empty = ModeSnapshot(False, "", None, "not fetched yet", now)
        self._lock = threading.Lock()
        self._state = State(
            time_text=initial_time_text,
            current_mode="weather",
            current_mode_duration_s=10,
            weather=empty,
            bus=empty,
            excuse=empty,
            message=empty,
        )

    def get(self) -> State:
        with self._lock:
            return self._state

    def update(self, **kwargs) -> None:
        with self._lock:
            for k, v in kwargs.items():
                setattr(self._state, k, v)

    def as_dict(self) -> dict:
        return asdict(self.get())
