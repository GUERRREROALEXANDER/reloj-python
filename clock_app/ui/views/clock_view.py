"""Main screen: the analog clock with a digital read-out."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

from ...features import format_duration
from ..analog_clock import AnalogClock
from ..widgets import Card, RoundedButton, ToggleSwitch
from .base import View


class ClockView(View):
    title = "Clock"
    icon = "clock"
    shortcut = "1"

    def build(self) -> None:
        t = self.theme
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2, minsize=330)
        self.rowconfigure(0, weight=1)

        self.clock = AnalogClock(self, t, self.fonts, self.app.engine, self.app.dial_styles.current)
        self.clock.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        side = tk.Frame(self, bg=t.background)
        side.grid(row=0, column=1, sticky="nsew")
        side.columnconfigure(0, weight=1)

        # Digital time card.
        time_card = Card(side, t, padding=24, height=212)
        time_card.grid(row=0, column=0, sticky="ew")
        body = time_card.body
        self.section_title(body, "Local time").pack(anchor="w")
        row = tk.Frame(body, bg=t.surface)
        row.pack(anchor="w", pady=(6, 0))
        self.time_label = self.label(row, "", 48, family=self.fonts.light)
        self.time_label.pack(side="left")
        self.seconds_label = self.label(row, "", 22, color=t.accent, family=self.fonts.light)
        self.seconds_label.pack(side="left", anchor="s", pady=(0, 12), padx=(4, 0))
        self.period_label = self.label(row, "", 14, "bold", t.text_muted, family=self.fonts.semibold)
        self.period_label.pack(side="left", anchor="s", pady=(0, 14), padx=(8, 0))
        self.date_label = self.label(body, "", 12, color=t.text_muted)
        self.date_label.pack(anchor="w")
        self.zone_label = self.label(body, "", 9, "bold", t.text_muted)
        self.zone_label.pack(anchor="w", pady=(6, 0))

        # Settings card.
        settings = Card(side, t, padding=22, height=190)
        settings.grid(row=1, column=0, sticky="ew", pady=14)
        sbody = settings.body
        sbody.columnconfigure(0, weight=1)
        self.section_title(sbody, "Display").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self._setting_row(sbody, 1, "Smooth second hand", self.app.engine.smooth_seconds, self._toggle_smooth)
        self._setting_row(sbody, 2, "24-hour format", self.app.settings["use_24h"], self._toggle_24h)

        self.label(sbody, "Dial style", 11).grid(row=3, column=0, sticky="w", pady=(10, 0))
        dial_row = tk.Frame(sbody, bg=t.surface)
        dial_row.grid(row=3, column=1, sticky="e", pady=(10, 0))
        RoundedButton(dial_row, t, self.fonts, "‹", self._previous_dial, "secondary",
                      width=34, height=30, bg=t.surface).pack(side="left")
        self.dial_label = self.label(dial_row, self.app.dial_styles.current.name, 10, "bold",
                                     width=9, family=self.fonts.semibold)
        self.dial_label.pack(side="left")
        RoundedButton(dial_row, t, self.fonts, "›", self._next_dial, "secondary",
                      width=34, height=30, bg=t.surface).pack(side="left")

        # Status card.
        status = Card(side, t, padding=22, height=186)
        status.grid(row=2, column=0, sticky="ew")
        stbody = status.body
        stbody.columnconfigure(1, weight=1)
        self.section_title(stbody, "At a glance").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.next_alarm_value = self._status_row(stbody, 1, "Next alarm")
        self.timer_value = self._status_row(stbody, 2, "Timer")
        self.stopwatch_value = self._status_row(stbody, 3, "Stopwatch")
        self.week_value = self._status_row(stbody, 4, "Day / week")

    def _setting_row(self, master, row, text, value, command) -> None:
        self.label(master, text, 11).grid(row=row, column=0, sticky="w", pady=4)
        ToggleSwitch(master, self.theme, value, command, bg=self.theme.surface).grid(row=row, column=1, sticky="e")

    def _status_row(self, master, row, text) -> tk.Label:
        self.label(master, text, 10, color=self.theme.text_muted).grid(row=row, column=0, sticky="w", pady=3)
        value = self.label(master, "—", 10, "bold", family=self.fonts.semibold)
        value.grid(row=row, column=1, sticky="e", pady=3)
        return value

    # ----------------------------------------------------------- actions
    def _toggle_smooth(self, value: bool) -> None:
        self.app.engine.smooth_seconds = value

    def _toggle_24h(self, value: bool) -> None:
        self.app.settings["use_24h"] = value

    def _next_dial(self) -> None:
        self._apply_dial(self.app.dial_styles.next())

    def _previous_dial(self) -> None:
        self._apply_dial(self.app.dial_styles.previous())

    def _apply_dial(self, style) -> None:
        self.dial_label.configure(text=style.name)
        self.clock.set_dial_style(style)

    # ----------------------------------------------------------- refresh
    def refresh(self, now: datetime) -> None:
        self.clock.refresh()
        if self.app.settings["use_24h"]:
            self.time_label.configure(text=now.strftime("%H:%M"))
            self.period_label.configure(text="")
        else:
            self.time_label.configure(text=f"{now.hour % 12 or 12}:{now.minute:02d}")
            self.period_label.configure(text="AM" if now.hour < 12 else "PM")
        self.seconds_label.configure(text=f"{now.second:02d}")
        self.date_label.configure(text=now.strftime("%A, %d %B %Y"))
        self.zone_label.configure(text=f"{self.app.engine.provider.offset_label()}  ·  synced with system clock")

        upcoming = self.app.alarms.next_alarm(now.replace(tzinfo=None))
        if upcoming:
            alarm, when = upcoming
            delta = when - now.replace(tzinfo=None)
            self.next_alarm_value.configure(
                text=f"{alarm.time_text(self.app.settings['use_24h'])} · in {format_duration(delta.total_seconds(), False)}"
            )
        else:
            self.next_alarm_value.configure(text="None")
        self.timer_value.configure(text=self.app.timer.summary())
        self.stopwatch_value.configure(text=self.app.stopwatch.summary())
        iso = now.isocalendar()
        self.week_value.configure(text=f"Day {now.timetuple().tm_yday} · Week {iso.week}")

    def on_key(self, event: tk.Event) -> bool:
        if event.keysym.lower() == "d":
            self._next_dial()
            return True
        return False
