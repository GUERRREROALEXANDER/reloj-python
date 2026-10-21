"""Ringing dialog and sound playback."""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from .theme import Fonts, Theme, blend
from .widgets import RoundedButton, draw_rounded_rect

try:
    import winsound
except ImportError:  # not on Windows
    winsound = None


class Chime:
    """Plays a repeating alert sound without blocking the UI."""

    def __init__(self, widget: tk.Misc, interval_ms: int = 1400) -> None:
        self.widget = widget
        self.interval_ms = interval_ms
        self._job: str | None = None

    def start(self) -> None:
        self._play()

    def _play(self) -> None:
        if winsound is not None:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        else:
            self.widget.bell()
        self._job = self.widget.after(self.interval_ms, self._play)

    def stop(self) -> None:
        if self._job is not None:
            self.widget.after_cancel(self._job)
            self._job = None
        if winsound is not None:
            winsound.PlaySound(None, winsound.SND_PURGE)


class RingingDialog(tk.Toplevel):
    """Borderless always-on-top card announcing an alarm or a finished timer."""

    WIDTH, HEIGHT = 380, 300

    def __init__(
        self,
        master: tk.Misc,
        theme: Theme,
        fonts: Fonts,
        title: str,
        message: str,
        on_dismiss: Callable[[], None],
        on_snooze: Callable[[], None] | None = None,
        snooze_text: str = "Snooze 5 min",
    ) -> None:
        super().__init__(master)
        self.theme = theme
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        transparent = "#010203"
        self.configure(bg=transparent)
        try:
            self.attributes("-transparentcolor", transparent)
        except tk.TclError:
            pass

        master.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.WIDTH) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.HEIGHT) // 2
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        canvas = tk.Canvas(self, width=self.WIDTH, height=self.HEIGHT, bg=transparent, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        draw_rounded_rect(canvas, 2, 2, self.WIDTH - 2, self.HEIGHT - 2, 26,
                          fill=theme.surface, outline=theme.accent, width=2)
        cx = self.WIDTH / 2
        self._halo = [canvas.create_oval(cx - r, 70 - r, cx + r, 70 + r, outline=blend(theme.surface, theme.accent, a), width=2)
                      for r, a in ((44, 0.15), (36, 0.3))]
        canvas.create_oval(cx - 28, 42, cx + 28, 98, fill=theme.accent, outline=theme.accent)
        draw_bell(canvas, cx, 70, 15, theme.accent_text)
        canvas.create_text(cx, 128, text=title, fill=theme.text, font=fonts(20, "bold", fonts.semibold))
        canvas.create_text(cx, 160, text=message, fill=theme.text_muted, font=fonts(11), width=self.WIDTH - 60,
                           justify="center")

        self.chime = Chime(self)
        self._on_dismiss, self._on_snooze = on_dismiss, on_snooze
        buttons = tk.Frame(canvas, bg=theme.surface)
        if on_snooze:
            RoundedButton(buttons, theme, fonts, snooze_text, self._snooze, "secondary",
                          width=150, height=44, bg=theme.surface).pack(side="left", padx=6)
        RoundedButton(buttons, theme, fonts, "Dismiss", self._dismiss, "primary",
                      width=150, height=44, bg=theme.surface).pack(side="left", padx=6)
        canvas.create_window(cx, 236, window=buttons)

        self._canvas = canvas
        self._pulse_step = 0
        self._pulse()
        self.chime.start()
        # "break" keeps these keys away from the global shortcuts.
        self.bind("<Key>", lambda _e: "break")
        self.bind("<Escape>", lambda _e: (self._dismiss(), "break")[1])
        self.bind("<Return>", lambda _e: (self._dismiss(), "break")[1])
        self.focus_force()

    def _pulse(self) -> None:
        self._pulse_step = (self._pulse_step + 1) % 20
        k = abs(10 - self._pulse_step) / 10
        for i, item in enumerate(self._halo):
            amount = (0.1 + 0.35 * k) * (1 - i * 0.4)
            self._canvas.itemconfigure(item, outline=blend(self.theme.surface, self.theme.accent, amount))
        self._pulse_job = self.after(60, self._pulse)

    def _close(self) -> None:
        self.chime.stop()
        self.after_cancel(self._pulse_job)
        self.destroy()

    def _dismiss(self) -> None:
        self._close()
        self._on_dismiss()

    def _snooze(self) -> None:
        self._close()
        if self._on_snooze:
            self._on_snooze()


def draw_bell(canvas: tk.Canvas, cx: float, cy: float, s: float, color: str) -> None:
    canvas.create_polygon(
        cx - s * 0.75, cy + s * 0.55, cx - s * 0.6, cy + s * 0.3, cx - s * 0.6, cy - s * 0.15,
        cx - s * 0.45, cy - s * 0.65, cx, cy - s * 0.85, cx + s * 0.45, cy - s * 0.65,
        cx + s * 0.6, cy - s * 0.15, cx + s * 0.6, cy + s * 0.3, cx + s * 0.75, cy + s * 0.55,
        fill=color, outline=color, smooth=True,
    )
    canvas.create_rectangle(cx - s * 0.8, cy + s * 0.48, cx + s * 0.8, cy + s * 0.6, fill=color, outline=color)
    canvas.create_oval(cx - s * 0.2, cy + s * 0.6, cx + s * 0.2, cy + s * 0.95, fill=color, outline=color)
