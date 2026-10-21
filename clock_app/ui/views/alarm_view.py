"""Alarm list and editor."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

from ...features import Alarm
from ...features.alarm import WEEKDAY_NAMES
from ..theme import blend
from ..widgets import Card, Chip, RoundedButton, ScrollableFrame, Stepper, ToggleSwitch
from .base import View


class AlarmView(View):
    title = "Alarms"
    icon = "alarm"
    shortcut = "3"

    def build(self) -> None:
        t = self.theme
        self.alarms = self.app.alarms
        self.columnconfigure(0, weight=2, minsize=340)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(0, weight=1)

        # ------------------------------------------------------ editor card
        editor = Card(self, t, padding=24)
        editor.configure(height=480)
        editor.grid(row=0, column=0, sticky="new", padx=(0, 16))
        body = editor.body
        self.section_title(body, "New alarm").pack(anchor="w")

        now = datetime.now()
        steppers = tk.Frame(body, bg=t.surface)
        steppers.pack(pady=(14, 10))
        self.hour = Stepper(steppers, t, self.fonts, 23, now.hour, "hour")
        self.hour.pack(side="left", padx=6)
        self.label(steppers, ":", 26, color=t.text_muted, family=self.fonts.light).pack(side="left")
        self.minute = Stepper(steppers, t, self.fonts, 59, (now.minute + 1) % 60, "minute")
        self.minute.pack(side="left", padx=6)

        self.label(body, "Label", 9, "bold", t.text_muted).pack(anchor="w", pady=(8, 4))
        self.name_entry = tk.Entry(
            body, bg=t.surface_alt, fg=t.text, insertbackground=t.text, relief="flat",
            font=self.fonts(12), highlightthickness=1, highlightbackground=t.border, highlightcolor=t.accent,
        )
        self.name_entry.insert(0, "Wake up")
        self.name_entry.pack(fill="x", ipady=8)

        self.label(body, "Repeat", 9, "bold", t.text_muted).pack(anchor="w", pady=(14, 6))
        days = tk.Frame(body, bg=t.surface)
        days.pack(anchor="w")
        self.day_chips = [Chip(days, t, self.fonts, name[:2], False) for name in WEEKDAY_NAMES]
        for chip in self.day_chips:
            chip.pack(side="left", padx=(0, 4))
        self.label(body, "No days selected = every day", 8, color=t.text_muted).pack(anchor="w", pady=(4, 0))

        RoundedButton(body, t, self.fonts, "Add alarm", self._add, "primary", width=290, height=44,
                      bg=t.surface).pack(pady=(18, 0))
        self.feedback = self.label(body, "", 9, color=t.success)
        self.feedback.pack(pady=(8, 0))

        # ------------------------------------------------------- list column
        right = tk.Frame(self, bg=t.background)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        banner = Card(right, t, padding=20, height=96, fill=blend(t.surface, t.accent, 0.12))
        banner.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        bbody = banner.body
        self.banner_title = self.label(bbody, "", 15, "bold", family=self.fonts.semibold)
        self.banner_title.pack(anchor="w")
        self.banner_caption = self.label(bbody, "", 10, color=t.text_muted)
        self.banner_caption.pack(anchor="w", pady=(2, 0))

        self.list_frame = ScrollableFrame(right, t.background)
        self.list_frame.grid(row=1, column=0, sticky="nsew")

        self.alarms.subscribe(self._on_alarm_event)
        self.bind("<Destroy>", lambda e: self.alarms.unsubscribe(self._on_alarm_event) if e.widget is self else None)
        self._render()

    # --------------------------------------------------------- actions
    def _add(self) -> None:
        days = frozenset(i for i, chip in enumerate(self.day_chips) if chip.selected)
        alarm = self.alarms.add(self.hour.value, self.minute.value, self.name_entry.get(), days)
        self.feedback.configure(text=f"Alarm set for {alarm.time_text(self.app.settings['use_24h'])}")
        self.after(2500, lambda: self.feedback.winfo_exists() and self.feedback.configure(text=""))

    def _on_alarm_event(self, event: str, _payload) -> None:
        if event == "changed":
            self._render()

    def _render(self) -> None:
        t = self.theme
        for child in self.list_frame.inner.winfo_children():
            child.destroy()
        if not len(self.alarms):
            empty = tk.Frame(self.list_frame.inner, bg=t.background)
            empty.pack(fill="x", pady=60)
            self.label(empty, "No alarms yet", 14, "bold", family=self.fonts.semibold).pack()
            self.label(empty, "Create one with the form on the left.", 10, color=t.text_muted).pack(pady=(4, 0))
            return
        for alarm in self.alarms:
            self._alarm_row(alarm)
        self.list_frame.scroll_to_top()

    def _alarm_row(self, alarm: Alarm) -> None:
        t = self.theme
        card = Card(self.list_frame.inner, t, padding=16, height=86, radius=16)
        card.pack(fill="x", pady=(0, 10))
        body = card.body
        body.columnconfigure(1, weight=1)
        dim = t.text if alarm.enabled else t.text_muted
        use_24h = self.app.settings["use_24h"]
        self.label(body, alarm.time_text(use_24h), 26, color=dim, family=self.fonts.light).grid(
            row=0, column=0, rowspan=2, sticky="w", padx=(4, 18))
        self.label(body, alarm.label, 12, "bold", dim, family=self.fonts.semibold).grid(row=0, column=1, sticky="sw")
        details = alarm.days_text()
        if alarm.snoozed_until:
            details += f"  ·  snoozed until {alarm.snoozed_until:%H:%M}"
        self.label(body, details, 9, color=t.text_muted).grid(row=1, column=1, sticky="nw")
        ToggleSwitch(body, t, alarm.enabled, lambda _v, a=alarm: self.alarms.toggle(a.id), bg=t.surface).grid(
            row=0, column=2, rowspan=2, padx=8)
        RoundedButton(body, t, self.fonts, "✕", lambda a=alarm: self.alarms.remove(a.id), "ghost",
                      width=34, height=34, bg=t.surface).grid(row=0, column=3, rowspan=2)
        for widget in (card, body):
            self.list_frame.bind_all_wheel(widget)

    # --------------------------------------------------------- refresh
    def refresh(self, now: datetime) -> None:
        naive = now.replace(tzinfo=None)
        upcoming = self.alarms.next_alarm(naive)
        if upcoming:
            alarm, when = upcoming
            seconds = (when - naive).total_seconds()
            hours, rest = divmod(int(seconds), 3600)
            minutes = rest // 60 + (1 if rest % 60 else 0)
            if minutes == 60:
                hours, minutes = hours + 1, 0
            span = f"{hours} h {minutes} min" if hours else f"{minutes} min"
            self.banner_title.configure(text=f"Next alarm in {span}")
            self.banner_caption.configure(
                text=f"{alarm.label}  ·  {when:%A} at {alarm.time_text(self.app.settings['use_24h'])}")
        else:
            self.banner_title.configure(text="No active alarms")
            self.banner_caption.configure(text=f"{len(self.alarms)} alarm(s) saved  ·  all switched off"
                                          if len(self.alarms) else "Your schedule is clear")

    def subtitle(self, now: datetime) -> str:
        return self.alarms.summary()

    def on_key(self, event: tk.Event) -> bool:
        if event.keysym == "Return" and event.widget is not self.name_entry:
            self._add()
            return True
        return False
