from __future__ import annotations

import os
import time
import threading

from config.secrets import secrets
from config.device import device

from utils import set_tz, clock_text, is_quiet_hours
from state import StateStore
from fetchers import Fetcher
from layout import compute_mode_duration_s
from web import create_app
from control import Control
from matrix.renderer import Renderer


MODE_ORDER = ["weather", "bus", "excuse", "message"]


def next_mode(mode: str) -> str:
    i = MODE_ORDER.index(mode)
    return MODE_ORDER[(i + 1) % len(MODE_ORDER)]


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
            except Exception:
                pass
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
        st = store.get()
        snap = getattr(st, mode, None)
        if snap is None:
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

                store.update(time_text=clock_text())

                st = store.get()

                # Quiet hours
                quiet_active = False
                if device.QUIET_HOURS_ENABLED:
                    quiet_active = is_quiet_hours(device.OFF_START, device.ON_START)

                desired_power = st.power_on
                if device.QUIET_HOURS_ENABLED:
                    desired_power = not quiet_active

                if desired_power != st.power_on:
                    store.update(power_on=desired_power)
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
