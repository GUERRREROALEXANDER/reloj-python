"""Clock hands.

Each concrete hand decides which part of the time it reads and how it looks,
while the shared base class keeps a cursor over its own dial ring. The views
just iterate over ``Hand`` objects and ask each one for its angle and shape.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from .dial import DialRing


@dataclass(frozen=True)
class HandStyle:
    length: float        # fraction of the dial radius
    tail: float          # counterweight length, fraction of the radius
    width: float         # base width, fraction of the radius
    tip_width: float     # tip width, fraction of the radius
    color_key: str       # theme attribute holding the colour


class Hand(ABC):
    """Abstract clock hand that walks around a :class:`DialRing`."""

    style: HandStyle

    def __init__(self, ring_size: int) -> None:
        self.ring = DialRing(ring_size)
        self._cursor = self.ring.cursor()
        self._fraction = 0.0

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def read(self, moment: datetime) -> tuple[int, float]:
        """Return ``(position, fraction)`` of this hand for ``moment``."""

    def update(self, moment: datetime) -> None:
        position, fraction = self.read(moment)
        # Normal ticking moves the cursor one node forward; a jump (new city,
        # clock adjustment) uses the bidirectional seek over the ring.
        current = self._cursor.node
        if current is not None and current.value.index != position:
            if current.next.value.index == position:
                self._cursor.forward()
            else:
                self._cursor.seek(lambda mark: mark.index == position)
        self._fraction = fraction

    @property
    def position(self) -> int:
        return self._cursor.value.index

    @property
    def angle(self) -> float:
        """Angle in degrees, clockwise from 12 o'clock."""
        return (self.position + self._fraction) * 360.0 / self.ring.size

    def polygon(self, cx: float, cy: float, radius: float) -> list[float]:
        """Return the outline of the hand as a flat list of canvas coordinates.

        The default shape is a tapered blade; subclasses can override it.
        """
        s = self.style
        rad = math.radians(self.angle)
        ux, uy = math.sin(rad), -math.cos(rad)   # unit vector to the tip
        px, py = -uy, ux                         # perpendicular

        tip = (cx + ux * radius * s.length, cy + uy * radius * s.length)
        tail = (cx - ux * radius * s.tail, cy - uy * radius * s.tail)
        half_base = radius * s.width / 2
        half_tip = radius * s.tip_width / 2
        neck = 0.82

        points = [
            (tail[0] + px * half_base, tail[1] + py * half_base),
            (cx + ux * radius * s.length * neck + px * half_tip, cy + uy * radius * s.length * neck + py * half_tip),
            tip,
            (cx + ux * radius * s.length * neck - px * half_tip, cy + uy * radius * s.length * neck - py * half_tip),
            (tail[0] - px * half_base, tail[1] - py * half_base),
        ]
        return [coord for point in points for coord in point]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(position={self.position}, angle={self.angle:.1f})"


class HourHand(Hand):
    style = HandStyle(length=0.50, tail=0.10, width=0.065, tip_width=0.045, color_key="hour_hand")

    def __init__(self) -> None:
        super().__init__(12)

    @property
    def name(self) -> str:
        return "hour"

    def read(self, moment: datetime) -> tuple[int, float]:
        minutes = moment.minute + moment.second / 60
        return moment.hour % 12, minutes / 60


class MinuteHand(Hand):
    style = HandStyle(length=0.74, tail=0.12, width=0.045, tip_width=0.030, color_key="minute_hand")

    def __init__(self) -> None:
        super().__init__(60)

    @property
    def name(self) -> str:
        return "minute"

    def read(self, moment: datetime) -> tuple[int, float]:
        seconds = moment.second + moment.microsecond / 1_000_000
        return moment.minute, seconds / 60


class SecondHand(Hand):
    """Thin hand with a counterweight; can sweep smoothly or tick."""

    style = HandStyle(length=0.86, tail=0.20, width=0.012, tip_width=0.012, color_key="second_hand")

    def __init__(self, smooth: bool = True) -> None:
        super().__init__(60)
        self.smooth = smooth

    @property
    def name(self) -> str:
        return "second"

    def read(self, moment: datetime) -> tuple[int, float]:
        fraction = moment.microsecond / 1_000_000 if self.smooth else 0.0
        return moment.second, fraction

    def polygon(self, cx: float, cy: float, radius: float) -> list[float]:
        # A straight line from the counterweight to the tip.
        s = self.style
        rad = math.radians(self.angle)
        ux, uy = math.sin(rad), -math.cos(rad)
        return [
            cx - ux * radius * s.tail, cy - uy * radius * s.tail,
            cx + ux * radius * s.length, cy + uy * radius * s.length,
        ]

    def counterweight(self, cx: float, cy: float, radius: float) -> tuple[float, float]:
        rad = math.radians(self.angle)
        distance = radius * self.style.tail * 0.75
        return cx - math.sin(rad) * distance, cy + math.cos(rad) * distance
