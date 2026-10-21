"""Countdown timer screen."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime, timedelta

from ...features import format_duration
from ..widgets import Card, ProgressRing, RoundedButton, Stepper
from .base import View


def preset_text(seconds: int) -> str:
    return f"{seconds // 3600} h" if seconds >= 3600 and seconds % 3600 == 0 else f"{seconds // 60} min"


class TimerView(View):
    title = "Timer"
    icon = "timer"
    shortcut = "5"

    def build(self) -> None:
        t = self.theme
        self.timer = self.app.timer
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2, minsize=330)
        self.rowconfigure(0, weight=1)

        left = tk.Frame(self, bg=t.background)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.ring = ProgressRing(left, t, self.fonts)
        self.ring.grid(row=0, column=0, sticky="nsew")

        buttons = tk.Frame(left, bg=t.background)
        buttons.grid(row=1, column=0, pady=(8, 4))
        self.reset_button = RoundedButton(buttons, t, self.fonts, "Reset", self.timer.reset, "secondary", width=120, height=46)
        self.reset_button.pack(side="left", padx=6)
        self.start_button = RoundedButton(buttons, t, self.fonts, "Start", self.timer.toggle, "primary", width=150, height=46)
        self.start_button.pack(side="left", padx=6)
        RoundedButton(buttons, t, self.fonts, "+1 min", lambda: self.timer.add_time(60), "secondary",
                      width=120, height=46).pack(side="left", padx=6)
        self.label(left, "Space  start / pause     R  reset     ← →  presets", 9, color=t.text_muted).grid(
            row=2, column=0, pady=(6, 0))

        side = tk.Frame(self, bg=t.background)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)

        presets = Card(side, t, padding=22, height=150)
        presets.grid(row=0, column=0, sticky="ew")
        pbody = presets.body
        self.section_title(pbody, "Quick presets").pack(anchor="w")
        carousel = tk.Frame(pbody, bg=t.surface)
        carousel.pack(fill="x", pady=(14, 0))
        RoundedButton(carousel, t, self.fonts, "‹", self._previous_preset, "secondary",
                      width=44, height=44, bg=t.surface).pack(side="left")
        self.preset_label = self.label(carousel, "", 22, family=self.fonts.light)
        self.preset_label.pack(side="left", expand=True)
        RoundedButton(carousel, t, self.fonts, "›", self._next_preset, "secondary",
                      width=44, height=44, bg=t.surface).pack(side="right")

        custom = Card(side, t, padding=22, height=290)
        custom.grid(row=1, column=0, sticky="ew", pady=14)
        cbody = custom.body
        self.section_title(cbody, "Custom duration").pack(anchor="w")
        steppers = tk.Frame(cbody, bg=t.surface)
        steppers.pack(pady=(10, 12))
        self.hours = Stepper(steppers, t, self.fonts, 23, 0, "hours")
        self.minutes = Stepper(steppers, t, self.fonts, 59, 5, "minutes")
        self.seconds = Stepper(steppers, t, self.fonts, 59, 0, "seconds", step=5)
        for i, stepper in enumerate((self.hours, self.minutes, self.seconds)):
            if i:
                self.label(steppers, ":", 26, color=t.text_muted, family=self.fonts.light).pack(side="left", padx=2)
            stepper.pack(side="left", padx=6)
        RoundedButton(cbody, t, self.fonts, "Set timer", self._apply_custom, "primary",
                      width=280, height=42, bg=t.surface).pack()

        self._sync_steppers()

    def _sync_steppers(self) -> None:
        total = int(self.timer.duration)
        self.hours.set(total // 3600)
        self.minutes.set(total % 3600 // 60)
        self.seconds.set(total % 60)
        self.preset_label.configure(text=preset_text(self.timer.preset_cursor.value))

    def _next_preset(self) -> None:
        self.timer.next_preset()
        self._sync_steppers()

    def _previous_preset(self) -> None:
        self.timer.previous_preset()
        self._sync_steppers()

    def _apply_custom(self) -> None:
        total = self.hours.value * 3600 + self.minutes.value * 60 + self.seconds.value
        if total > 0:
            self.timer.set_duration(total)

    def refresh(self, now: datetime) -> None:
        tm = self.timer
        remaining = tm.remaining
        if tm.finished:
            caption, color = "TIME'S UP", self.theme.danger
        elif tm.running:
            ends = now + timedelta(seconds=remaining)
            caption, color = f"ENDS AT {ends:%H:%M}", self.theme.accent
        elif remaining < tm.duration:
            caption, color = "PAUSED", self.theme.text_muted
        else:
            caption, color = f"OF {format_duration(tm.duration, False)}", self.theme.accent
        title = format_duration(remaining + (0.99 if tm.running else 0), show_centis=False)
        self.ring.update_ring(1 - tm.progress, title, caption, color)
        self.start_button.set_text("Pause" if tm.running else ("Resume" if 0 < remaining < tm.duration else "Start"))
        self.reset_button.set_enabled(not tm.running and remaining != tm.duration)

    def subtitle(self, now: datetime) -> str:
        return "Count down to zero and get notified"

    def on_key(self, event: tk.Event) -> bool:
        key = event.keysym.lower()
        if key == "space":
            self.timer.toggle()
        elif key == "r":
            self.timer.reset()
        elif key == "right":
            self._next_preset()
        elif key == "left":
            self._previous_preset()
        else:
            return False
        return True
