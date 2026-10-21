"""Analog clock canvas and interchangeable dial styles."""

from __future__ import annotations

import math
import tkinter as tk
from abc import ABC, abstractmethod
from typing import Optional

from ..core import ClockEngine, DialRing, SecondHand
from ..structures import CircularDoublyLinkedList, RingCursor
from .theme import Fonts, Theme, blend


class DialStyle(ABC):
    """Decides how the hour positions of the face are labelled."""

    name: str = "Dial"

    @abstractmethod
    def label(self, hour: int) -> Optional[str]:
        """Text for hour position ``hour`` (12 for the top), or ``None``."""

    def numeral_scale(self) -> float:
        return 0.11

    def numeral_radius(self) -> float:
        return 0.70

    def draws_minor_ticks(self) -> bool:
        return True


class ArabicDial(DialStyle):
    name = "Classic"

    def label(self, hour: int) -> Optional[str]:
        return str(hour)


class RomanDial(DialStyle):
    name = "Roman"
    NUMERALS = ("XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI")

    def label(self, hour: int) -> Optional[str]:
        return self.NUMERALS[hour % 12]

    def numeral_scale(self) -> float:
        return 0.085


class QuarterDial(DialStyle):
    name = "Quarters"

    def label(self, hour: int) -> Optional[str]:
        return str(hour) if hour % 3 == 0 else None

    def numeral_scale(self) -> float:
        return 0.15

    def numeral_radius(self) -> float:
        return 0.66


class MinimalDial(DialStyle):
    name = "Minimal"

    def label(self, hour: int) -> Optional[str]:
        return None

    def draws_minor_ticks(self) -> bool:
        return False


class DialStyleCarousel:
    """Cycles through dial styles using a circular doubly linked list."""

    def __init__(self) -> None:
        self.styles: CircularDoublyLinkedList[DialStyle] = CircularDoublyLinkedList(
            (ArabicDial(), RomanDial(), QuarterDial(), MinimalDial())
        )
        self._cursor = RingCursor(self.styles)

    @property
    def current(self) -> DialStyle:
        return self._cursor.value

    def next(self) -> DialStyle:
        return self._cursor.forward()

    def previous(self) -> DialStyle:
        return self._cursor.backward()


class AnalogClock(tk.Canvas):
    """Draws a :class:`ClockEngine` as an analog clock.

    The face is drawn once per resize; on every frame only the coordinates of
    the hands change, which keeps the animation smooth.
    """

    MINUTE_RING = DialRing(60)

    def __init__(
        self,
        master: tk.Misc,
        theme: Theme,
        fonts: Fonts,
        engine: ClockEngine,
        dial_style: Optional[DialStyle] = None,
        compact: bool = False,
        bg: Optional[str] = None,
        caption: str = "",
        **kwargs,
    ) -> None:
        super().__init__(master, bg=bg or theme.background, highlightthickness=0, bd=0, **kwargs)
        self.theme = theme
        self.fonts = fonts
        self.engine = engine
        self.dial_style = dial_style or ArabicDial()
        self.compact = compact
        self.caption = caption
        self._geometry = (0.0, 0.0, 0.0)
        self.bind("<Configure>", lambda _e: self.redraw())

    # ----------------------------------------------------------------- face
    def set_dial_style(self, style: DialStyle) -> None:
        self.dial_style = style
        self.redraw()

    def set_engine(self, engine: ClockEngine) -> None:
        self.engine = engine
        self.refresh()

    def redraw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        margin = 10 if self.compact else 28
        r = (min(w, h) - 2 * margin) / 2
        if r < 20:
            return
        cx, cy = w / 2, h / 2
        self._geometry = (cx, cy, r)
        t = self.theme
        bg = self["bg"]

        # Drop shadow made of fading rings, shifted slightly downwards.
        layers = 4 if self.compact else 12
        for i in range(layers, 0, -1):
            spread = r * 0.006 * i
            shade = blend(bg, t.hand_shadow, 0.5 * (1 - i / (layers + 1)) ** 1.6)
            self.create_oval(cx - r - spread, cy - r - spread + r * 0.02,
                             cx + r + spread, cy + r + spread + r * 0.03, fill=shade, outline=shade)

        # Rim with a subtle bevel.
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=t.face_rim, outline=t.face_rim)
        bevel = r * 0.035
        self.create_oval(cx - r + bevel, cy - r + bevel, cx + r - bevel, cy + r - bevel,
                         fill=blend(t.face_rim, t.face_outer, 0.5), outline="")

        # Face: radial gradient from the outer to the inner colour.
        face_r = r * (0.93 if not self.compact else 0.92)
        steps = 10 if self.compact else 24
        for i in range(steps):
            k = i / steps
            rr = face_r * (1 - k * 0.9)
            color = blend(t.face_outer, t.face_inner, k ** 0.7)
            self.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, fill=color, outline=color)

        self._draw_ticks(cx, cy, face_r)
        if not self.compact:
            self._draw_numerals(cx, cy, face_r)
            self.create_text(cx, cy - face_r * 0.34, text="CHRONOS", fill=blend(t.face_inner, t.numeral, 0.55),
                             font=self.fonts(max(7, int(face_r * 0.045)), "bold", self.fonts.semibold))
            self.create_text(cx, cy + face_r * 0.36, text="", fill=t.second_hand,
                             font=self.fonts(max(8, int(face_r * 0.05)), "bold", self.fonts.semibold), tags="date")
        elif self.caption:
            self.create_text(cx, cy + face_r * 0.42, text=self.caption, fill=blend(t.face_inner, t.numeral, 0.6),
                             font=self.fonts(max(7, int(face_r * 0.12)), "bold", self.fonts.semibold))

        self._create_hand_items(face_r)
        self.refresh()

    def _draw_ticks(self, cx: float, cy: float, face_r: float) -> None:
        t = self.theme
        minor = self.dial_style.draws_minor_ticks() or self.compact
        # The 60 positions come straight from the dial ring.
        for mark in self.MINUTE_RING:
            if not mark.is_major and not minor:
                continue
            angle = math.radians(mark.angle)
            sin, cos = math.sin(angle), -math.cos(angle)
            outer = face_r * 0.95
            if mark.is_major:
                inner = face_r * (0.83 if not self.compact else 0.80)
                width = max(2, face_r * (0.022 if mark.index % 15 == 0 else 0.016))
                color = t.tick_major
            else:
                if self.compact:
                    continue
                inner = face_r * 0.905
                width = max(1, face_r * 0.007)
                color = t.tick_minor
            self.create_line(cx + sin * inner, cy + cos * inner, cx + sin * outer, cy + cos * outer,
                             fill=color, width=width, capstyle="round")

    def _draw_numerals(self, cx: float, cy: float, face_r: float) -> None:
        style = self.dial_style
        size = max(9, int(face_r * style.numeral_scale()))
        radius = face_r * style.numeral_radius()
        for mark in DialRing(12):
            hour = mark.index or 12
            text = style.label(hour)
            if text is None:
                continue
            angle = math.radians(mark.angle)
            self.create_text(cx + math.sin(angle) * radius, cy - math.cos(angle) * radius, text=text,
                             fill=self.theme.numeral, font=self.fonts(size, "normal", self.fonts.display))

    # ---------------------------------------------------------------- hands
    def _create_hand_items(self, face_r: float) -> None:
        t = self.theme
        for hand in self.engine.hands:
            color = getattr(t, hand.style.color_key)
            if isinstance(hand, SecondHand):
                width = max(1.5, face_r * 0.012)
                self.create_line(0, 0, 0, 0, fill=t.hand_shadow, width=width, capstyle="round", tags="second_shadow")
                self.create_line(0, 0, 0, 0, fill=color, width=width, capstyle="round", tags="second")
                self.create_oval(0, 0, 0, 0, fill=color, outline=color, tags="second_weight")
            else:
                self.create_polygon(0, 0, 0, 0, fill=t.hand_shadow, outline="", tags=f"{hand.name}_shadow")
                self.create_polygon(0, 0, 0, 0, fill=color, outline=color, tags=hand.name)
        pin = face_r * 0.045
        cx, cy, _ = self._geometry
        self.create_oval(cx - pin, cy - pin, cx + pin, cy + pin, fill=t.pin, outline=t.pin)
        inner = pin * 0.45
        self.create_oval(cx - inner, cy - inner, cx + inner, cy + inner,
                         fill=t.face_inner, outline=t.face_inner)

    def refresh(self) -> None:
        cx, cy, r = self._geometry
        if r <= 0:
            return
        face_r = r * 0.93
        shadow = face_r * 0.018
        for hand in self.engine.hands:
            points = hand.polygon(cx, cy, face_r)
            shadow_points = [p + shadow * (1 if i % 2 else 0.6) for i, p in enumerate(points)]
            self.coords(f"{hand.name}_shadow", *shadow_points)
            self.coords(hand.name, *points)
            if isinstance(hand, SecondHand):
                wx, wy = hand.counterweight(cx, cy, face_r)
                wr = face_r * 0.03
                self.coords("second_weight", wx - wr, wy - wr, wx + wr, wy + wr)
        if not self.compact:
            moment = self.engine.moment
            self.itemconfigure("date", text=moment.strftime("%a %d").upper())
