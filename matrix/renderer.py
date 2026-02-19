from __future__ import annotations

import io
import time
import threading
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from config import device
from state import StateStore
from matrix_output import MatrixOutput


class Renderer:
    def __init__(self, store: StateStore) -> None:
        self.store = store
        self.w = device.MATRIX_WIDTH_PX
        self.h = device.MATRIX_HEIGHT_PX
        self.text_w = device.TEXT_AREA_WIDTH_PX

        self.out = MatrixOutput(self.w, self.h)

        self.img = Image.new("RGB", (self.w, self.h), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        self.font = ImageFont.truetype(device.FONT_PATH, device.FONT_SIZE_PX)

        self._lock = threading.Lock()
        self._latest_png: bytes = b""

        self._last_mode: str = ""
        self._last_text: str = ""
        self._scroll_started_at: float = time.time()

    def get_preview_png(self) -> bytes:
        with self._lock:
            return self._latest_png

    def _save_preview(self) -> None:
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        with self._lock:
            self._latest_png = bio.getvalue()

    def _text_width_px(self, s: str) -> int:
        if not s:
            return 0
        box = self.draw.textbbox((0, 0), s, font=self.font)
        return int(box[2] - box[0])

    def _clear(self) -> None:
        self.draw.rectangle((0, 0, self.w, self.h), fill=(0, 0, 0))

    def _draw_clock(self, time_text: str) -> None:
        clock_color = (0, 255, 100)
        w_clock = self._text_width_px(time_text)
        x_clock = max(device.CLOCK_START_X_PX, self.w - w_clock)

        self.draw.rectangle(
            (device.CLOCK_START_X_PX, 0, self.w, self.h),
            fill=(0, 0, 0),
        )
        self.draw.text((x_clock, -1), time_text, font=self.font, fill=clock_color)

    def _draw_mode_text(self, mode: str, text: str) -> None:
        colors = {
            "weather": (0, 150, 255),
            "bus": (255, 180, 0),
            "excuse": (255, 100, 255),
            "message": (255, 255, 0),
        }
        color = colors.get(mode, (255, 255, 255))

        self.draw.rectangle((0, 0, self.text_w, self.h), fill=(0, 0, 0))

        w_text = self._text_width_px(text)
        needs_scroll = w_text > self.text_w

        now = time.time()
        if mode != self._last_mode or text != self._last_text:
            self._scroll_started_at = now
            self._last_mode = mode
            self._last_text = text

        if not needs_scroll:
            self.draw.text((0, -1), text, font=self.font, fill=color)
            return

        pause_s = device.SCROLL_START_PAUSE_S
        gap_px = device.SCROLL_GAP_PX
        speed_px_s = device.SCROLL_SPEED_PX_S

        t = max(0.0, now - self._scroll_started_at - pause_s)
        cycle_px = w_text + gap_px
        x = int(-((t * speed_px_s) % cycle_px))

        self.draw.text((x, -1), text, font=self.font, fill=color)
        self.draw.text((x + cycle_px, -1), text, font=self.font, fill=color)

    def tick(self) -> None:
        st = self.store.get()

        if getattr(st, "power_on", True) is False:
            self.out.blackout()
            self._clear()
            self._save_preview()
            return

        mode = st.current_mode
        time_text = st.time_text or ""

        snap = getattr(st, mode, None)
        display_text = (snap.display_text or "") if snap else ""

        self._clear()
        self._draw_mode_text(mode, display_text)
        self._draw_clock(time_text)

        self.out.show_frame(self.img)
        self._save_preview()
