from __future__ import annotations

import os
import time
import threading

from config import (
    WEATHER_URL,
    BUS_URL,
    EXCUSES_URL,
    MESSAGE_URL,
    NEXT_URL,
    TZ,
    FETCH_INTERVAL_S,
    BASE_MODE_DURATIONS_S,
    EMPTY_MESSAGE_DURATION_S,
)

from utils import set_tz, clock_text
from state import StateStore
from fetchers import Fetcher
from layout import compute_mode_duration_s
from web import create_app


MODE_ORDER = ["weather", "bus", "excuse", "message"]


def next_mode(mode: str) -> str:
    i = MODE_ORDER.index(mode)
    return MODE_ORDER[(i + 1) % len(MODE_ORDER)]


def main() -> None:
    set_tz(TZ)

    store = StateStore(initial_time_text=clock_text())
    fetcher = Fetcher(
        weather_url=WEATHER_URL,
        bus_url=BUS_URL,
        excuses_url=EXCUSES_URL,
        message_url=MESSAGE_URL,
        next_url=NEXT_URL,
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

    def background_loop() -> None:
        nonlocal current_mode, mode_started_at, last_fetch_at

        while True:
            now = time.time()

            store.update(time_text=clock_text())

            if now - last_fetch_at >= FETCH_INTERVAL_S:
                try:
                    do_fetch_all()
                except Exception:
                    pass
                last_fetch_at = now

            display_text = get_display_text_for_mode(current_mode)
            base_s = int(BASE_MODE_DURATIONS_S.get(current_mode, 10))
            dur_s = compute_mode_duration_s(
                current_mode,
                display_text,
                base_s=base_s,
                empty_message_s=EMPTY_MESSAGE_DURATION_S,
            )

            store.update(current_mode=current_mode, current_mode_duration_s=dur_s)

            if now - mode_started_at >= dur_s:
                current_mode = next_mode(current_mode)
                mode_started_at = now

            time.sleep(0.25)

    t = threading.Thread(target=background_loop, daemon=True)
    t.start()

    app = create_app(store)
    host = os.environ.get("BIND_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
