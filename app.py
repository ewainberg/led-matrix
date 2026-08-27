from __future__ import annotations

import os
import re
import time
import threading

import config.secrets as secrets
import config.device as device

from utils import set_tz, clock_text, is_quiet_hours, is_time_reminder_active
from state import StateStore
from fetchers import Fetcher
from layout import compute_mode_duration_s
from web import create_app
from control import Control
from matrix.renderer import Renderer
from matrix.scene_builder import (
    make_bus_takeover_presentation,
    make_time_reminder_presentation,
)


MODE_ORDER = ["weather", "bus", "excuse", "message"]
BUS_INTERRUPT_THRESHOLD_MIN = 2


def next_mode(mode: str) -> str:
    i = MODE_ORDER.index(mode)
    return MODE_ORDER[(i + 1) % len(MODE_ORDER)]


def parse_bus_eta_minutes(display_text: str) -> int | None:
    s = (display_text or "").strip().lower()
    if not s:
        return None

    matches = re.findall(r"(\d+)\s*m\b", s)
    if not matches:
        return None

    return min(int(x) for x in matches)


def main() -> None:
    set_tz(device.TZ)

    weather_url = (
        f"{device.WEATHER_BASE_URL}/current.json"
        f"?key={secrets.WEATHER_KEY}&q={device.WEATHER_LOCATION}"
    )

    store = StateStore(initial_time_text=clock_text())
    renderer = Renderer(store)

    def render_loop() -> None:
        dt = 1.0 / float(device.RENDER_FPS)
        while True:
            try:
                renderer.tick()
            except Exception as e:
                store.update(last_error=f"render: {type(e).__name__}: {e}")
            time.sleep(dt)

    threading.Thread(target=render_loop, daemon=True).start()

    fetcher = Fetcher(
        weather_url=weather_url,
        bus_url=device.BUS_URL,
        excuses_url=device.EXCUSES_URL,
        message_url=device.MESSAGE_URL,
        next_url=secrets.NEXT_URL,
        timeout_s=8,
    )

    current_mode = "weather"
    mode_started_at = time.time()
    last_fetch_at = 0.0

    def get_display_text_for_mode(mode: str) -> str:
        if mode == "time_reminder":
            return getattr(device, "TIME_REMINDER_TEXT", "TURN IN YOUR TIME")
        st = store.get()
        snap = getattr(st, mode, None)
        if snap is None or not hasattr(snap, "display_text"):
            return ""
        return snap.display_text or ""

    def do_fetch_all() -> None:
        store.update(
            weather=fetcher.fetch_weather(),
            bus=fetcher.fetch_bus(),
            excuse=fetcher.fetch_excuse(),
            message=fetcher.fetch_message(),
        )

    ctl = Control()

    def background_loop() -> None:
        nonlocal current_mode, mode_started_at, last_fetch_at
        while True:
            try:
                now = time.time()

                # ----------------------------------------------------------
                # Tetris mode — skip all normal display logic while active
                # ----------------------------------------------------------
                tetris_game = getattr(store.get(), "tetris_game", None)
                if tetris_game is not None:
                    tetris_game.tick()
                    time.sleep(0.25)
                    continue
                # ----------------------------------------------------------

                store.update(time_text=clock_text())

                st = store.get()

                quiet_active = False
                if device.QUIET_HOURS_ENABLED:
                    quiet_active = is_quiet_hours(device.OFF_START, device.ON_START)

                if quiet_active != st.quiet_hours_active:
                    store.update(quiet_hours_active=quiet_active)
                    store.update(power_on=(not quiet_active))
                    st = store.get()

                if ctl.consume_refresh():
                    do_fetch_all()
                    last_fetch_at = now

                if now - last_fetch_at >= device.FETCH_INTERVAL_S:
                    do_fetch_all()
                    last_fetch_at = now

                st = store.get()
                active_mode = st.forced_mode or current_mode

                display_text = get_display_text_for_mode(active_mode)

                bus_text = get_display_text_for_mode("bus")
                bus_eta_min = parse_bus_eta_minutes(bus_text)

                time_reminder_active = False
                if getattr(device, "TIME_REMINDER_ENABLED", True) and not quiet_active:
                    day_of_week = getattr(device, "TIME_REMINDER_DAY", 3)
                    interval_m = getattr(device, "TIME_REMINDER_INTERVAL_M", 5)
                    duration_s = getattr(device, "TIME_REMINDER_DURATION_S", 12)
                    time_reminder_active = is_time_reminder_active(
                        day_of_week=day_of_week,
                        interval_m=interval_m,
                        duration_s=duration_s,
                    )

                if bus_eta_min is not None and bus_eta_min <= BUS_INTERRUPT_THRESHOLD_MIN:
                    store.update(
                        override_presentation=make_bus_takeover_presentation(bus_text)
                    )
                elif time_reminder_active or getattr(st, "time_reminder", False):
                    reminder_text = getattr(device, "TIME_REMINDER_TEXT", "TURN IN YOUR TIME")
                    store.update(
                        override_presentation=make_time_reminder_presentation(reminder_text)
                    )
                else:
                    store.update(override_presentation=None)

                base_s = int(device.BASE_MODE_DURATIONS_S.get(active_mode, 10))
                dur_s = compute_mode_duration_s(
                    active_mode,
                    display_text,
                    base_s=base_s,
                    empty_message_s=device.EMPTY_MESSAGE_DURATION_S,
                )

                store.update(current_mode=active_mode, current_mode_duration_s=dur_s)

                if not st.rotation_paused:
                    if now - mode_started_at >= dur_s:
                        if st.forced_mode:
                            mode_started_at = now
                        else:
                            current_mode = next_mode(current_mode)
                            mode_started_at = now

            except Exception as e:
                store.update(last_error=f"loop: {type(e).__name__}: {e}")

            time.sleep(0.25)

    t = threading.Thread(target=background_loop, daemon=True)
    t.start()

    app = create_app(store, ctl, preview_png_provider=renderer.get_preview_png)
    host = os.environ.get("BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()