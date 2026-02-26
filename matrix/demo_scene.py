from __future__ import annotations

from PIL import ImageFont

from matrix.ctx import Viewport
from matrix.pipeline import DrawUnit
from matrix.primitives.frame import FramePrimitive
from matrix.primitives.text import TextPrimitive
from matrix.primitives.arrows import ArrowStripPrimitive
from matrix.effects.dash import Dash
from matrix.effects.phase import PhaseShiftWrap
from matrix.effects.transform import Wave, Bounce


def build_demo_scene(
    idx: int,
    *,
    font: ImageFont.FreeTypeFont,
    screen_w: int,
    screen_h: int,
    text_w: int,
    clock_start_x: int,
) -> list[DrawUnit]:
    vp_text = Viewport(0, 0, text_w, screen_h)
    vp_clock = Viewport(clock_start_x, 0, screen_w - clock_start_x, screen_h)

    i = idx % 6
    units: list[DrawUnit] = []

    if i == 0:
        units.append(DrawUnit(vp=vp_text, prim=FramePrimitive((80, 80, 80)), effects=[]))
        units.append(DrawUnit(
            vp=vp_text,
            prim=TextPrimitive("SOLID FRAME", font, (255, 255, 255), mode="static", y_align="center"),
            effects=[],
        ))

    elif i == 1:
        units.append(DrawUnit(vp=vp_text, prim=FramePrimitive((80, 80, 80)), effects=[Dash(2, 2, 0.0)]))
        units.append(DrawUnit(
            vp=vp_text,
            prim=TextPrimitive("DOTTED", font, (255, 255, 255), mode="static", y_align="center"),
            effects=[],
        ))

    elif i == 2:
        units.append(DrawUnit(vp=vp_text, prim=FramePrimitive((80, 80, 80)), effects=[Dash(2, 2, 14.0)]))
        units.append(DrawUnit(
            vp=vp_text,
            prim=TextPrimitive("MARCHING", font, (255, 255, 255), mode="static", y_align="center"),
            effects=[],
        ))

    elif i == 3:
        units.append(DrawUnit(
            vp=vp_clock,
            prim=ArrowStripPrimitive((0, 255, 0), direction="up", spacing=3),
            effects=[PhaseShiftWrap(axis="y", speed_px_s=6.0, direction=1)],
        ))
        units.append(DrawUnit(
            vp=vp_text,
            prim=TextPrimitive("ARROWS UP", font, (255, 255, 255), mode="static", y_align="center"),
            effects=[],
        ))

    elif i == 4:
        units.append(DrawUnit(
            vp=vp_text,
            prim=TextPrimitive("WAVE SCROLL DEMO TEXT", font, (255, 200, 0), mode="scroll", y_align="center"),
            effects=[Wave(axis="y", amplitude_px=1, period_px=18, speed_px_s=10.0)],
        ))

    else:
        units.append(DrawUnit(
            vp=vp_text,
            prim=TextPrimitive("BOUNCE", font, (255, 255, 255), mode="static", y_align="center"),
            effects=[Bounce(axis="y", amplitude_px=1, period_s=0.45)],
        ))

    return units