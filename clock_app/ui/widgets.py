"""Custom Tkinter widgets drawn on canvases."""

from __future__ import annotations

import math
import tkinter as tk
from typing import Callable, Optional

from .theme import Fonts, Theme, blend


def rounded_rect_points(x1: float, y1: float, x2: float, y2: float, r: float) -> list[float]:
    """Control points for a rounded rectangle drawn with ``smooth=True``."""
    r = max(0.0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]


def draw_rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kwargs) -> int:
    return canvas.create_polygon(rounded_rect_points(x1, y1, x2, y2, r), smooth=True, **kwargs)


class ThemedCanvas(tk.Canvas):
    """Canvas that blends with its parent's background."""

    def __init__(self, master: tk.Misc, theme: Theme, bg: Optional[str] = None, **kwargs) -> None:
        super().__init__(master, highlightthickness=0, bd=0, bg=bg or theme.background, **kwargs)
        self.theme = theme


class RoundedButton(ThemedCanvas):
    """Pill-shaped button with hover and pressed states.

    ``variant`` selects the colour role: primary, secondary, ghost or danger.
    """

    def __init__(
        self,
        master: tk.Misc,
        theme: Theme,
        fonts: Fonts,
        text: str,
        command: Callable[[], None] | None = None,
        variant: str = "primary",
        width: int = 120,
        height: int = 42,
        radius: int | None = None,
        font_size: int = 11,
        bg: Optional[str] = None,
    ) -> None:
        super().__init__(master, theme, bg=bg, width=width, height=height, cursor="hand2")
        self.fonts = fonts
        self.command = command
        self.variant = variant
        self._text = text
        self._radius = height / 2 if radius is None else radius
        self._font = fonts(font_size, "bold", fonts.semibold)
        self._hover = False
        self._pressed = False
        self._enabled = True
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda _e: self._draw())
        self._draw()

    def _colors(self) -> tuple[str, str, str]:
        t = self.theme
        if self.variant == "primary":
            fill, fg, outline = t.accent, t.accent_text, t.accent
            if self._hover:
                fill = outline = t.accent_hover
        elif self.variant == "danger":
            fill, fg, outline = blend(t.surface, t.danger, 0.16), t.danger, blend(t.surface, t.danger, 0.4)
            if self._hover:
                fill = blend(t.surface, t.danger, 0.28)
        elif self.variant == "ghost":
            fill, fg, outline = self["bg"], t.text_muted, self["bg"]
            if self._hover:
                fill = outline = blend(self["bg"], t.text, 0.08)
                fg = t.text
        else:
            fill, fg, outline = t.surface_alt, t.text, t.border
            if self._hover:
                fill = blend(t.surface_alt, t.text, 0.07)
        if self._pressed:
            fill = blend(fill, "#000000", 0.15)
        if not self._enabled:
            fill = blend(fill, self["bg"], 0.55)
            fg = blend(fg, self["bg"], 0.55)
            outline = blend(outline, self["bg"], 0.55)
        return fill, fg, outline

    def _draw(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1:
            w, h = int(self["width"]), int(self["height"])
        fill, fg, outline = self._colors()
        offset = 1 if self._pressed else 0
        draw_rounded_rect(self, 1, 1 + offset, w - 1, h - 1, self._radius, fill=fill, outline=outline)
        self.create_text(w / 2, h / 2 + offset, text=self._text, fill=fg, font=self._font)

    def _set_hover(self, value: bool) -> None:
        self._hover = value
        if not value:
            self._pressed = False
        self._draw()

    def _on_press(self, _event) -> None:
        if self._enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, event) -> None:
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        if was_pressed and inside and self._enabled and self.command:
            self.command()

    def set_text(self, text: str) -> None:
        if text != self._text:
            self._text = text
            self._draw()

    def set_variant(self, variant: str) -> None:
        if variant != self.variant:
            self.variant = variant
            self._draw()

    def set_enabled(self, enabled: bool) -> None:
        if enabled != self._enabled:
            self._enabled = enabled
            self.configure(cursor="hand2" if enabled else "arrow")
            self._draw()


class ToggleSwitch(ThemedCanvas):
    """iOS-style on/off switch."""

    def __init__(
        self,
        master: tk.Misc,
        theme: Theme,
        value: bool = False,
        command: Callable[[bool], None] | None = None,
        bg: Optional[str] = None,
    ) -> None:
        super().__init__(master, theme, bg=bg, width=46, height=26, cursor="hand2")
        self.value = value
        self.command = command
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        t = self.theme
        track = t.accent if self.value else blend(t.surface_alt, t.text, 0.15)
        draw_rounded_rect(self, 1, 1, 45, 25, 12, fill=track, outline=track)
        x = 33 if self.value else 13
        knob = "#ffffff" if self.value or not t.dark else blend(t.text, t.surface, 0.2)
        self.create_oval(x - 9, 4, x + 9, 22, fill=knob, outline=knob)

    def _toggle(self, _event=None) -> None:
        self.set(not self.value)
        if self.command:
            self.command(self.value)

    def set(self, value: bool) -> None:
        self.value = value
        self._draw()


class Card(ThemedCanvas):
    """Rounded surface; put child widgets inside ``card.body``."""

    def __init__(
        self,
        master: tk.Misc,
        theme: Theme,
        padding: int = 20,
        radius: int = 18,
        fill: Optional[str] = None,
        bg: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, theme, bg=bg, **kwargs)
        self.fill = fill or theme.surface
        self.padding = padding
        self.radius = radius
        self.body = tk.Frame(self, bg=self.fill)
        self._window = self.create_window(padding, padding, window=self.body, anchor="nw")
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event) -> None:
        self.delete("shape")
        draw_rounded_rect(
            self, 1, 1, event.width - 1, event.height - 1, self.radius,
            fill=self.fill, outline=blend(self.fill, self.theme.border, 0.6), tags="shape",
        )
        self.tag_lower("shape")
        self.itemconfigure(
            self._window,
            width=max(1, event.width - 2 * self.padding),
            height=max(1, event.height - 2 * self.padding),
        )


class ProgressRing(ThemedCanvas):
    """Circular progress indicator with centred title and caption."""

    def __init__(self, master: tk.Misc, theme: Theme, fonts: Fonts, bg: Optional[str] = None, **kwargs) -> None:
        super().__init__(master, theme, bg=bg, **kwargs)
        self.fonts = fonts
        self.progress = 0.0
        self.title = ""
        self.caption = ""
        self.color = theme.accent
        self.dot = True
        self._geometry = (0.0, 0.0, 0.0)
        self.bind("<Configure>", lambda _e: self._draw_static())

    def _draw_static(self) -> None:
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        size = min(w, h) - 24
        if size <= 40:
            return
        cx, cy, r = w / 2, h / 2, size / 2
        self._geometry = (cx, cy, r)
        thickness = max(8, size * 0.035)
        track = blend(self["bg"], self.theme.text, 0.08)
        # Soft halo behind the ring for depth.
        for i in range(6, 0, -1):
            pad = thickness * 0.4 * i
            self.create_oval(cx - r - pad, cy - r - pad, cx + r + pad, cy + r + pad,
                             outline=blend(self["bg"], self.color, 0.015 * (7 - i)), width=2)
        self.create_oval(cx - r, cy - r, cx + r, cy + r, outline=track, width=thickness)
        for i in range(60):
            angle = math.radians(i * 6)
            inner = r - thickness * (2.2 if i % 5 == 0 else 1.6)
            outer = r - thickness * 1.2
            self.create_line(
                cx + math.sin(angle) * inner, cy - math.cos(angle) * inner,
                cx + math.sin(angle) * outer, cy - math.cos(angle) * outer,
                fill=blend(self["bg"], self.theme.text, 0.25 if i % 5 == 0 else 0.1), width=2,
            )
        self.create_arc(cx - r, cy - r, cx + r, cy + r, start=90, extent=0, style="arc",
                        outline=self.color, width=thickness, tags="arc")
        self.create_oval(0, 0, 0, 0, fill=self.color, outline=self["bg"], width=3, tags="dot")
        self.create_text(cx, cy - size * 0.03, text="", fill=self.theme.text,
                         font=self.fonts(max(18, int(size * 0.13)), "normal", self.fonts.light), tags="title")
        self.create_text(cx, cy + size * 0.12, text="", fill=self.theme.text_muted,
                         font=self.fonts(max(10, int(size * 0.035)), "bold", self.fonts.semibold), tags="caption")
        self.update_ring(self.progress, self.title, self.caption)

    def update_ring(self, progress: float, title: str, caption: str = "", color: Optional[str] = None) -> None:
        self.progress = max(0.0, min(1.0, progress))
        self.title, self.caption = title, caption
        if color and color != self.color:
            self.color = color
            self._draw_static()
            return
        cx, cy, r = self._geometry
        if r <= 0:
            return
        extent = -359.99 * self.progress
        self.itemconfigure("arc", extent=extent)
        thickness = max(8, r * 2 * 0.035)
        angle = math.radians(self.progress * 360)
        dx, dy = cx + math.sin(angle) * r, cy - math.cos(angle) * r
        dot_r = thickness * 0.9 if self.dot and self.progress > 0 else 0
        self.coords("dot", dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r)
        self.itemconfigure("title", text=title)
        self.itemconfigure("caption", text=caption)


class ScrollableFrame(tk.Frame):
    """Vertical scroll container with mouse-wheel support and no scrollbar chrome."""

    def __init__(self, master: tk.Misc, bg: str) -> None:
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.pack(fill="both", expand=True)
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))
        self.bind_all_wheel(self.canvas)
        self.bind_all_wheel(self.inner)

    def bind_all_wheel(self, widget: tk.Misc) -> None:
        widget.bind("<Enter>", lambda _e: self.canvas.bind_all("<MouseWheel>", self._on_wheel))
        widget.bind("<Leave>", lambda _e: self.canvas.unbind_all("<MouseWheel>"))

    def _on_wheel(self, event) -> None:
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def scroll_to_top(self) -> None:
        self.canvas.yview_moveto(0)


class Stepper(tk.Frame):
    """Large numeric field with up/down arrows (used for hours, minutes...)."""

    def __init__(
        self,
        master: tk.Misc,
        theme: Theme,
        fonts: Fonts,
        maximum: int,
        value: int = 0,
        caption: str = "",
        bg: Optional[str] = None,
        step: int = 1,
        on_change: Callable[[int], None] | None = None,
    ) -> None:
        bg = bg or theme.surface
        super().__init__(master, bg=bg)
        self.theme, self.maximum, self.step = theme, maximum, step
        self.value = value
        self.on_change = on_change
        arrow_font = fonts(10, "bold")
        self._up = tk.Label(self, text="▲", bg=bg, fg=theme.text_muted, font=arrow_font, cursor="hand2")
        self._label = tk.Label(self, text=f"{value:02d}", bg=theme.surface_alt, fg=theme.text,
                               font=fonts(30, "normal", fonts.light), width=3, pady=4)
        self._down = tk.Label(self, text="▼", bg=bg, fg=theme.text_muted, font=arrow_font, cursor="hand2")
        self._up.pack()
        self._label.pack(pady=2)
        self._down.pack()
        if caption:
            tk.Label(self, text=caption.upper(), bg=bg, fg=theme.text_muted, font=fonts(8, "bold")).pack(pady=(4, 0))
        for widget, delta in ((self._up, step), (self._down, -step)):
            widget.bind("<Button-1>", lambda _e, d=delta: self.change(d))
            widget.bind("<Enter>", lambda _e, w=widget: w.configure(fg=theme.accent))
            widget.bind("<Leave>", lambda _e, w=widget: w.configure(fg=theme.text_muted))
        self._label.bind("<MouseWheel>", lambda e: self.change(self.step if e.delta > 0 else -self.step))

    def change(self, delta: int) -> None:
        self.set((self.value + delta) % (self.maximum + 1))
        if self.on_change:
            self.on_change(self.value)

    def set(self, value: int) -> None:
        self.value = value
        self._label.configure(text=f"{value:02d}")


class Chip(tk.Label):
    """Small toggleable pill label."""

    def __init__(self, master: tk.Misc, theme: Theme, fonts: Fonts, text: str,
                 selected: bool = False, command: Callable[[bool], None] | None = None,
                 bg: Optional[str] = None) -> None:
        super().__init__(master, text=text, font=fonts(9, "bold"), padx=10, pady=5, cursor="hand2")
        self.theme = theme
        self.selected = selected
        self.command = command
        self._bg = bg or theme.surface
        self.bind("<Button-1>", self._toggle)
        self._paint()

    def _paint(self) -> None:
        t = self.theme
        if self.selected:
            self.configure(bg=t.accent, fg=t.accent_text)
        else:
            self.configure(bg=t.surface_alt, fg=t.text_muted)

    def _toggle(self, _event=None) -> None:
        self.set(not self.selected)
        if self.command:
            self.command(self.selected)

    def set(self, selected: bool) -> None:
        self.selected = selected
        self._paint()
