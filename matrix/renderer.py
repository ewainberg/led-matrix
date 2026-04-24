from __future__ import annotations

import io
import time
import threading

from PIL import Image, ImageDraw, ImageFont

from config import device
from state import StateStore
from matrix.matrix_output import MatrixOutput
from matrix.ctx import RenderContext
from matrix.scene_builder import (
    build_scene,
    Presentation,
    make_bread_alert_presentation,
    make_snake_alert_presentation,
)
from matrix.tetris_scene import render_tetris


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
        self.small_font = ImageFont.truetype(device.SMALL_FONT_PATH, device.SMALL_FONT_SIZE_PX)

        self._lock = threading.Lock()
        self._latest_png: bytes = b""

        self._last_scroll_key: tuple[str, str, bool, int] = ("", "", False, 0)
        self._scroll_started_at: float = time.time()

    def get_preview_png(self) -> bytes:
        with self._lock:
            return self._latest_png

    def _save_preview(self) -> None:
        bio = io.BytesIO()
        self.img.save(bio, format="PNG")
        with self._lock:
            self._latest_png = bio.getvalue()

    def _clear(self) -> None:
        self.draw.rectangle((0, 0, self.w, self.h), fill=(0, 0, 0))

    def tick(self) -> None:
        st = self.store.get()

        if getattr(st, "power_on", True) is False:
            self.out.blackout()
            self._clear()
            self._save_preview()
            return

        # ------------------------------------------------------------------
        # Tetris mode — takes full control, nothing else runs
        # ------------------------------------------------------------------
        tetris_game = getattr(st, "tetris_game", None)
        if tetris_game is not None:
            self._clear()
            now = time.time()
            ctx = RenderContext(
                img=self.img,
                draw=self.draw,
                t=now,
                screen_w=self.w,
                screen_h=self.h,
            )
            render_tetris(tetris_game, ctx)
            self.out.show_frame(self.img)
            self._save_preview()
            return
        # ------------------------------------------------------------------

        mode = st.current_mode
        time_text = st.time_text or ""
        snap = getattr(st, mode, None)
        display_text = (snap.display_text or "") if snap else ""

        engine_demo = bool(getattr(st, "engine_demo", False))
        engine_demo_idx = int(getattr(st, "engine_demo_idx", 0) or 0)
        alert = engine_demo

        presentation = getattr(st, "override_presentation", None)

        if presentation is None:
            if getattr(st, "snake_alert", False):
                presentation = make_snake_alert_presentation()
            elif getattr(st, "bread_alert", False):
                presentation = make_bread_alert_presentation()

        scroll_mode = presentation.mode if presentation else mode
        scroll_text = presentation.display_text if presentation else display_text
        scroll_alert = alert or (presentation is not None)

        now = time.time()
        key = (scroll_mode, scroll_text, scroll_alert, engine_demo_idx)
        if key != self._last_scroll_key:
            self._last_scroll_key = key
            self._scroll_started_at = now

        self._clear()

        ctx = RenderContext(
            img=self.img,
            draw=self.draw,
            t=now,
            screen_w=self.w,
            screen_h=self.h,
        )

        scene = build_scene(
            mode=mode,
            display_text=display_text,
            time_text=time_text,
            alert=alert,
            presentation=presentation,
            engine_demo_idx=engine_demo_idx,
            font=self.font,
            small_font=self.small_font,
            scroll_started_at=self._scroll_started_at,
            screen_w=self.w,
            screen_h=self.h,
            text_w=self.text_w,
        )

        for unit in scene:
            unit.draw(ctx)

        self.out.show_frame(self.img)
        self._save_preview()