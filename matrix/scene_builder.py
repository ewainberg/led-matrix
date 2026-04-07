from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from PIL import Image, ImageFont

from config import device
from matrix.ctx import RGB, Viewport
from matrix.pipeline import DrawUnit
from matrix.primitives.frame import FramePrimitive
from matrix.primitives.text import TextPrimitive
from matrix.primitives.sprite import SpritePrimitive
from matrix.primitives.spritesheet import SpriteSheetPrimitive
from matrix.primitives.sprite_scroll import VerticalSpriteScroller
from matrix.effects.dash import Dash
from matrix.weather_icons import get_weather_icon_path

PresentationKind = Literal["normal", "emphasis", "takeover", "alert", "bread_alert"]


@dataclass(slots=True)
class Presentation:
    kind: PresentationKind = "normal"
    mode: str = "message"
    display_text: str = ""
    time_text: str = ""

    show_clock: bool = True
    frame: bool = False
    full_width: bool = False
    use_small_font: bool = False

    color: tuple[int, int, int] | None = None
    frame_color: tuple[int, int, int] = (0, 255, 0)

    arrows: bool = False
    arrow_color: tuple[int, int, int] = (0, 255, 0)
    arrow_x: int | None = None
    arrow_y: int = 0

    sprite_path: str | None = None
    sprite_frame_width: int | None = None
    sprite_frame_height: int | None = None
    sprite_x: int = 0
    sprite_y: int = 0
    sprite_fps: float = 0.0
    sprite_color: tuple[int, int, int] | None = None

    text_inset_left: int = 0
    text_inset_right: int = 0
    center_text: bool = False
    text_y_offset: int = 0


MODE_COLORS = {
    "weather": (0, 150, 255),
    "bus": (255, 180, 0),
    "excuse": (255, 100, 255),
    "message": (255, 255, 0),
    "bread": (255, 0, 0),
}

BUS_COLOR = MODE_COLORS["bus"]
BUS_TAKEOVER_SPRITE_PATH = "/home/maxpower/ledmatrix/assets/bus.png"
BUS_TAKEOVER_SPRITE_FRAME_W = 12
BUS_TAKEOVER_SPRITE_FRAME_H = 6
BUS_TAKEOVER_SPRITE_FPS = 10.0

BREAD_COLOR = (255, 0, 0)
BREAD_ALERT_SPRITE_PATH = "/home/maxpower/ledmatrix/assets/bread.png"

WEATHER_ICON_W = 12
WEATHER_ICON_H = 8
WEATHER_TEXT_GAP = 1


def load_sprite_from_png(path: str, repeat: int = 4) -> list[list[Optional[RGB]]]:
    img = Image.open(path).convert("RGBA")
    px = img.load()
    w, h = img.size

    pixels: list[list[Optional[RGB]]] = []

    for _ in range(max(1, repeat)):
        for y in range(h):
            row: list[Optional[RGB]] = []
            for x in range(w):
                r, g, b, a = px[x, y]
                if a == 0:
                    row.append(None)
                else:
                    row.append((r, g, b))
            pixels.append(row)

    return pixels


def resolve_legacy_presentation(
    *,
    mode: str,
    display_text: str,
    time_text: str,
    alert: bool,
) -> Presentation:
    color = MODE_COLORS.get(mode, (255, 255, 255))

    if alert:
        return Presentation(
            kind="alert",
            mode=mode,
            display_text=display_text,
            time_text=time_text,
            show_clock=False,
            frame=True,
            full_width=True,
            use_small_font=True,
            color=color,
            frame_color=(0, 255, 0),
            arrows=True,
            arrow_color=(0, 255, 0),
        )

    return Presentation(
        kind="normal",
        mode=mode,
        display_text=display_text,
        time_text=time_text,
        show_clock=True,
        frame=False,
        full_width=False,
        use_small_font=False,
        color=color,
    )


def make_bus_takeover_presentation(display_text: str) -> Presentation:
    text = (display_text or "").strip()

    if text.lower().startswith("bus:"):
        suffix = text[4:].strip()
    else:
        suffix = text

    inbound_text = f"BUS INBOUND: {suffix}" if suffix else "BUS INBOUND"

    sprite_x = 2
    sprite_y = 1

    left_inset = sprite_x + BUS_TAKEOVER_SPRITE_FRAME_W + 1
    right_inset = 1

    return Presentation(
        kind="takeover",
        mode="bus",
        display_text=inbound_text,
        time_text="",
        show_clock=False,
        frame=True,
        full_width=True,
        use_small_font=True,
        center_text=True,
        text_y_offset=0,
        color=BUS_COLOR,
        frame_color=BUS_COLOR,
        arrows=False,
        sprite_path=BUS_TAKEOVER_SPRITE_PATH,
        sprite_frame_width=BUS_TAKEOVER_SPRITE_FRAME_W,
        sprite_frame_height=BUS_TAKEOVER_SPRITE_FRAME_H,
        sprite_x=sprite_x,
        sprite_y=sprite_y,
        sprite_fps=BUS_TAKEOVER_SPRITE_FPS,
        sprite_color=BUS_COLOR,
        text_inset_left=left_inset,
        text_inset_right=right_inset,
    )


def make_bread_alert_presentation() -> Presentation:
    return Presentation(
        kind="bread_alert",
        mode="bread",
        display_text="BREAD ALERT",
        time_text="",
        show_clock=False,
        frame=False,
        full_width=True,
        use_small_font=True,
        center_text=True,
        color=BREAD_COLOR,
        frame_color=BREAD_COLOR,
        arrows=False,
    )


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
    presentation: Presentation | None = None,
    **_,
) -> list[DrawUnit]:
    pres = presentation or resolve_legacy_presentation(
        mode=mode,
        display_text=display_text,
        time_text=time_text,
        alert=alert,
    )

    if pres.kind == "bread_alert":
        use_font = small_font if small_font is not None else font
        bread_pixels = load_sprite_from_png(BREAD_ALERT_SPRITE_PATH, repeat=6)

        one_screen_w = max(1, screen_w // 5)
        left_w = one_screen_w
        middle_x = left_w
        middle_w = max(1, one_screen_w * 3)
        right_x = left_w + middle_w
        right_w = max(1, screen_w - right_x)

        vp_left = Viewport(0, 0, left_w, screen_h)
        vp_middle = Viewport(middle_x, 0, middle_w, screen_h)
        vp_right = Viewport(right_x, 0, right_w, screen_h)

        frame_pad = 1
        vp_middle_text = Viewport(
            vp_middle.x + frame_pad,
            vp_middle.y + frame_pad,
            max(1, vp_middle.w - 2 * frame_pad),
            max(1, vp_middle.h - 2 * frame_pad),
        )

        return [
            DrawUnit(
                vp=vp_left,
                prim=VerticalSpriteScroller(
                    pixels=bread_pixels,
                    speed_px_s=10.0,
                    pause_s=0.0,
                    loop="wrap",
                ),
                effects=[],
            ),
            DrawUnit(
                vp=vp_right,
                prim=VerticalSpriteScroller(
                    pixels=bread_pixels,
                    speed_px_s=10.0,
                    pause_s=0.0,
                    loop="wrap",
                ),
                effects=[],
            ),
            DrawUnit(
                vp=vp_middle,
                prim=FramePrimitive(color=BREAD_COLOR, thickness=1),
                effects=[Dash(dash_len=2, gap_len=2, speed_px_s=20.0)],
            ),
            DrawUnit(
                vp=vp_middle_text,
                prim=TextPrimitive(
                    text="BREAD ALERT",
                    font=use_font,
                    color=BREAD_COLOR,
                    mode="static",
                    y_align="center",
                    x_align="center",
                ),
                effects=[],
            ),
        ]

    color = pres.color or MODE_COLORS.get(pres.mode, (255, 255, 255))
    use_font = small_font if (pres.use_small_font and small_font is not None) else font

    if pres.full_width or not pres.show_clock:
        vp_text_outer = Viewport(0, 0, screen_w, screen_h)
    else:
        vp_text_outer = Viewport(0, 0, text_w, screen_h)

    frame_pad = 1 if pres.frame else 0

    extra_right_inset = 0
    weather_icon_path = None

    if pres.mode == "weather":
        weather_icon_path = get_weather_icon_path(pres.display_text)
        if weather_icon_path:
            extra_right_inset = WEATHER_ICON_W + WEATHER_TEXT_GAP

    inner_x = vp_text_outer.x + frame_pad + pres.text_inset_left
    inner_y = vp_text_outer.y + frame_pad
    inner_w = max(
        1,
        vp_text_outer.w
        - (2 * frame_pad)
        - pres.text_inset_left
        - pres.text_inset_right
        - extra_right_inset,
    )
    inner_h = max(1, vp_text_outer.h - (2 * frame_pad))

    vp_text = Viewport(inner_x, inner_y + pres.text_y_offset, inner_w, inner_h)

    units: list[DrawUnit] = []

    x_align = "center" if pres.center_text else "left"

    if weather_icon_path:
        icon_x = vp_text_outer.w - WEATHER_ICON_W
        icon_y = max(0, (vp_text_outer.h - WEATHER_ICON_H) // 2)
        weather_pixels = load_sprite_from_png(weather_icon_path, repeat=1)
        units.append(
                    DrawUnit(
                        vp=Viewport(0, 0, screen_w, screen_h),
                        prim=SpritePrimitive(
                            pixels=weather_pixels,
                            x=icon_x,
                            y=icon_y,
                        ),
                        effects=[],
                    )
                )

    text_kwargs = dict(
        text=pres.display_text,
        font=use_font,
        color=color,
        mode="auto",
        start_pause_s=device.SCROLL_START_PAUSE_S,
        gap_px=device.SCROLL_GAP_PX,
        speed_px_s=device.SCROLL_SPEED_PX_S,
        y_align="center",
        x_align=x_align,
    )
    if scroll_started_at is not None:
        text_kwargs["scroll_started_at"] = scroll_started_at

    units.append(
        DrawUnit(
            vp=vp_text,
            prim=TextPrimitive(**text_kwargs),
            effects=[],
        )
    )

    if pres.show_clock:
        vp_clock = Viewport(
            device.CLOCK_START_X_PX,
            0,
            screen_w - device.CLOCK_START_X_PX,
            screen_h,
        )
        units.append(
            DrawUnit(
                vp=vp_clock,
                prim=TextPrimitive(
                    text=pres.time_text,
                    font=font,
                    color=(0, 255, 100),
                    mode="static",
                    y_align="center",
                    x_align="right",
                ),
                effects=[],
            )
        )

    if pres.frame:
        units.append(
            DrawUnit(
                vp=vp_text_outer,
                prim=FramePrimitive(color=pres.frame_color, thickness=1),
                effects=[Dash(dash_len=2, gap_len=2, speed_px_s=5.0)],
            )
        )

    if (
        pres.sprite_path
        and pres.sprite_frame_width is not None
        and pres.sprite_frame_height is not None
    ):
        units.append(
            DrawUnit(
                vp=vp_text_outer,
                prim=SpriteSheetPrimitive(
                    path=pres.sprite_path,
                    frame_width=pres.sprite_frame_width,
                    frame_height=pres.sprite_frame_height,
                    x=pres.sprite_x,
                    y=pres.sprite_y,
                    fps=pres.sprite_fps,
                    black_replacement=pres.sprite_color,
                ),
                effects=[],
            )
        )

    if pres.arrows:
        i = engine_demo_idx % 3
        if i == 0:
            arrow_x = pres.arrow_x if pres.arrow_x is not None else max(0, vp_text_outer.w - 8)
            units.append(
                DrawUnit(
                    vp=vp_text_outer,
                    prim=SpriteSheetPrimitive(
                        path="/home/maxpower/ledmatrix/assets/arrow.png",
                        frame_width=8,
                        frame_height=6,
                        x=arrow_x,
                        y=pres.arrow_y,
                        fps=6.0,
                        black_replacement=pres.arrow_color,
                    ),
                    effects=[],
                )
            )

    return units