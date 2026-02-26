from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Protocol

from matrix.ctx import RenderContext, Viewport, RGB


@dataclass
class Sample:
    x: int
    y: int
    on: bool = True
    color: Optional[RGB] = None
    meta_i: int = 0  # ordered index for marching/phase


class Effect(Protocol):
    def apply(self, s: Sample, ctx: RenderContext, vp: Viewport) -> Sample: ...


class Primitive(Protocol):
    def samples(self, ctx: RenderContext, vp: Viewport) -> Iterable[Sample]: ...


@dataclass
class DrawUnit:
    vp: Viewport
    prim: Primitive
    effects: list[Effect]

    def draw(self, ctx: RenderContext) -> None:
        for s in self.prim.samples(ctx, self.vp):
            for e in self.effects:
                s = e.apply(s, ctx, self.vp)
            if not s.on:
                continue
            if not self.vp.contains(s.x, s.y):
                continue
            ctx.putpixel(s.x, s.y, s.color or (255, 255, 255))