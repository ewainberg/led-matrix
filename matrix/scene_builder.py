from __future__ import annotations

from PIL import ImageFont

from config import device
from matrix.ctx import Viewport
from matrix.pipeline import DrawUnit
from matrix.primitives.frame import FramePrimitive
from matrix.primitives.text import TextPrimitive
from matrix.primitives.arrows import ArrowPrimitive
from matrix.effects.dash import Dash
from matrix.effects.local_wrap import LocalWrapShift

MODE_COLORS = {
    "weather": (0, 150, 255),
    "bus": (255, 180, 0),
    "excuse": (255, 100, 255),
    "message": (255, 255, 0),
}


def build_scene(
    *,
    mode: str,
    display_text: str,
    time_text: str,
    alert: bool,
    font: ImageFont.FreeTypeFont,
    small_font: ImageFont.FreeTypeFont | None = None,
    scroll_started_at: float | None = None,
    screen_w: int,
    screen_h: int,
    text_w: int,
    engine_demo_idx: int = 0,
    **_,
) -> list[DrawUnit]:
    # Alert = no clock area, full width usable.
    if alert:
        vp_text_outer = Viewport(0, 0, screen_w, screen_h)
    else:
        vp_text_outer = Viewport(0, 0, text_w, screen_h)

    units: list[DrawUnit] = []
    color = MODE_COLORS.get(mode, (255, 255, 255))
    use_font = small_font if (alert and small_font is not None) else font
    

    # If alert and you want a 1px frame, shrink inner text viewport
    if alert:
        vp_text = Viewport(vp_text_outer.x + 1, vp_text_outer.y + 1, vp_text_outer.w - 2, vp_text_outer.h - 2)
    else:
        vp_text = vp_text_outer

    # Text (scroll only if needed)
    text_kwargs = dict(
        text=display_text,
        font=use_font,
        color=color,
        mode="auto",
        start_pause_s=device.SCROLL_START_PAUSE_S,
        gap_px=device.SCROLL_GAP_PX,
        speed_px_s=device.SCROLL_SPEED_PX_S,
        y_align="center",
    )
    if scroll_started_at is not None:
        text_kwargs["scroll_started_at"] = scroll_started_at

    units.append(DrawUnit(vp=vp_text, prim=TextPrimitive(**text_kwargs), effects=[]))

    # Normal mode clock
    if not alert:
        vp_clock = Viewport(device.CLOCK_START_X_PX, 0, screen_w - device.CLOCK_START_X_PX, screen_h)
        units.append(
            DrawUnit(
                vp=vp_clock,
                prim=TextPrimitive(
                    text=time_text,
                    font=font,
                    color=(0, 255, 100),
                    mode="static",
                    y_align="center",
                    x_align="right",
                ),
                effects=[],
            )
        )

    # Alert extras
    if alert:
        # Frame around whole screen
        units.append(
            DrawUnit(
                vp=vp_text_outer,
                prim=FramePrimitive(color=(60, 60, 60), thickness=1),
                effects=[Dash(dash_len=2, gap_len=2, speed_px_s=14.0)],
            )
        )

        # Demo arrows: place anywhere inside vp_text_outer (not tied to clock)
        # engine_demo_idx can cycle layouts
        i = engine_demo_idx % 3
        if i == 0:
            # Left edge "UP" arrows
            units.append(DrawUnit(vp=vp_text_outer, prim=ArrowPrimitive("up", (0, 255, 0), x=1, y=1), effects=[]))
            units.append(DrawUnit(vp=vp_text_outer, prim=ArrowPrimitive("up", (0, 255, 0), x=1, y=screen_h - 6), effects=[]))
        elif i == 1:
            # Right edge "RIGHT" arrow
            units.append(
                DrawUnit(
                    vp=vp_text_outer,
                    prim=ArrowPrimitive("right", (0, 255, 0), x=vp_text_outer.w - 6, y=(screen_h - 5) // 2),
                    effects=[],
                )
            )
            units.append(
                DrawUnit(
                    vp=vp_text_outer,  # or any viewport you want
                    prim=ArrowPrimitive(direction="up", color=(0, 255, 0), x=10, y=1),
                    effects=[
                        # Wrap inside the arrow’s own 5x5 box so it “moves” but stays put
                        LocalWrapShift(axis="y", w=5, h=5, speed_px_s=6.0, direction=-1, origin_x=10, origin_y=1)
                    ],
                )
            )
        else:
            # Bottom-left "LEFT" arrow
            units.append(
                DrawUnit(
                    vp=vp_text_outer,
                    prim=ArrowPrimitive("left", (0, 255, 0), x=1, y=screen_h - 6),
                    effects=[],
                )
            )

    return units