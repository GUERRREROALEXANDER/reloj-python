"""Line icons drawn with canvas primitives (no image files needed)."""

from __future__ import annotations

import math
import tkinter as tk
from abc import ABC, abstractmethod


class Icon(ABC):
    """An icon knows how to draw itself centred on a point."""

    @abstractmethod
    def draw(self, canvas: tk.Canvas, cx: float, cy: float, size: float, color: str, width: float = 2) -> None: ...


class ClockIcon(Icon):
    def draw(self, canvas, cx, cy, size, color, width=2):
        r = size / 2
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)
        canvas.create_line(cx, cy, cx, cy - r * 0.6, fill=color, width=width, capstyle="round")
        canvas.create_line(cx, cy, cx + r * 0.45, cy + r * 0.2, fill=color, width=width, capstyle="round")


class GlobeIcon(Icon):
    def draw(self, canvas, cx, cy, size, color, width=2):
        r = size / 2
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)
        canvas.create_oval(cx - r * 0.42, cy - r, cx + r * 0.42, cy + r, outline=color, width=width)
        canvas.create_line(cx - r, cy, cx + r, cy, fill=color, width=width)


class AlarmIcon(Icon):
    def draw(self, canvas, cx, cy, size, color, width=2):
        r = size * 0.42
        cy += size * 0.06
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)
        canvas.create_line(cx, cy, cx, cy - r * 0.55, fill=color, width=width, capstyle="round")
        canvas.create_line(cx, cy, cx + r * 0.4, cy, fill=color, width=width, capstyle="round")
        for side in (-1, 1):
            canvas.create_arc(cx + side * r * 0.95 - r * 0.5, cy - r * 1.45, cx + side * r * 0.95 + r * 0.5,
                              cy - r * 0.45, start=45 if side > 0 else 90, extent=45, style="arc",
                              outline=color, width=width)


class StopwatchIcon(Icon):
    def draw(self, canvas, cx, cy, size, color, width=2):
        r = size * 0.42
        cy += size * 0.08
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)
        canvas.create_line(cx, cy - r, cx, cy - r * 1.3, fill=color, width=width)
        canvas.create_line(cx - r * 0.35, cy - r * 1.3, cx + r * 0.35, cy - r * 1.3, fill=color, width=width,
                           capstyle="round")
        angle = math.radians(40)
        canvas.create_line(cx, cy, cx + math.sin(angle) * r * 0.6, cy - math.cos(angle) * r * 0.6,
                           fill=color, width=width, capstyle="round")


class HourglassIcon(Icon):
    def draw(self, canvas, cx, cy, size, color, width=2):
        w, h = size * 0.36, size * 0.48
        canvas.create_line(cx - w, cy - h, cx + w, cy - h, fill=color, width=width, capstyle="round")
        canvas.create_line(cx - w, cy + h, cx + w, cy + h, fill=color, width=width, capstyle="round")
        canvas.create_line(cx - w * 0.8, cy - h, cx + w * 0.8, cy + h, fill=color, width=width)
        canvas.create_line(cx + w * 0.8, cy - h, cx - w * 0.8, cy + h, fill=color, width=width)
        canvas.create_polygon(cx - w * 0.45, cy + h * 0.85, cx + w * 0.45, cy + h * 0.85, cx, cy + h * 0.35,
                              fill=color, outline=color)


class ThemeIcon(Icon):
    def draw(self, canvas, cx, cy, size, color, width=2):
        r = size / 2
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)
        canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=90, extent=180, fill=color, outline=color)


ICONS: dict[str, Icon] = {
    "clock": ClockIcon(),
    "globe": GlobeIcon(),
    "alarm": AlarmIcon(),
    "stopwatch": StopwatchIcon(),
    "timer": HourglassIcon(),
    "theme": ThemeIcon(),
}
