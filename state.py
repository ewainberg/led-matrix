from __future__ import annotations

import time
import threading
from dataclasses import dataclass, asdict, replace
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
    power_on: bool
    rotation_paused: bool
    forced_mode: str  # "" means no forced mode
    last_error: str
    quiet_hours_active: bool
    engine_demo: bool
    engine_demo_idx: int
    bread_alert: bool
    bread_alert_changed_at: float


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
            power_on=True,
            rotation_paused=False,
            forced_mode="",
            last_error="",
            quiet_hours_active=False,
            engine_demo=False,
            engine_demo_idx=0,
            bread_alert=False,
            bread_alert_changed_at=0.0,
        )

    def get(self) -> State:
        with self._lock:
            return replace(self._state)

    def update(self, **kwargs) -> None:
        with self._lock:
            for k, v in kwargs.items():
                setattr(self._state, k, v)

    def as_dict(self) -> dict:
        return asdict(self.get())