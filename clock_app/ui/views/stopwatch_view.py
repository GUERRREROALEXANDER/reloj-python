"""Stopwatch screen."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime

from ...features import format_duration
from ..widgets import Card, ProgressRing, RoundedButton, ScrollableFrame
from .base import View


class StopwatchView(View):
    title = "Stopwatch"
    icon = "stopwatch"
    shortcut = "4"

    def build(self) -> None:
        t = self.theme
        self.stopwatch = self.app.stopwatch
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2, minsize=320)
        self.rowconfigure(0, weight=1)

        left = tk.Frame(self, bg=t.background)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.ring = ProgressRing(left, t, self.fonts)
        self.ring.grid(row=0, column=0, sticky="nsew")

        buttons = tk.Frame(left, bg=t.background)
        buttons.grid(row=1, column=0, pady=(8, 4))
        self.reset_button = RoundedButton(buttons, t, self.fonts, "Reset", self._reset, "secondary", width=120, height=46)
        self.reset_button.pack(side="left", padx=6)
        self.start_button = RoundedButton(buttons, t, self.fonts, "Start", self.stopwatch.toggle, "primary", width=150, height=46)
        self.start_button.pack(side="left", padx=6)
        self.lap_button = RoundedButton(buttons, t, self.fonts, "Lap", self._lap, "secondary", width=120, height=46)
        self.lap_button.pack(side="left", padx=6)
        self.label(left, "Space  start / pause     L  lap     R  reset", 9, color=t.text_muted).grid(row=2, column=0, pady=(6, 0))

        card = Card(self, t, padding=20)
        card.grid(row=0, column=1, sticky="nsew")
        body = card.body
        header = tk.Frame(body, bg=t.surface)
        header.pack(fill="x")
        self.section_title(header, "Laps").pack(side="left")
        self.lap_count = self.label(header, "", 9, "bold", t.text_muted)
        self.lap_count.pack(side="right")

        columns = self._grid_row(body, t.surface)
        columns.pack(fill="x", pady=(10, 4))
        for column, (text, anchor) in enumerate((("#", "w"), ("Split", "e"), ("Total", "e"))):
            self.label(columns, text, 9, "bold", t.text_muted, anchor=anchor, padx=10).grid(
                row=0, column=column, sticky="ew")
        tk.Frame(body, bg=t.border, height=1).pack(fill="x")

        self.lap_list = ScrollableFrame(body, t.surface)
        self.lap_list.pack(fill="both", expand=True, pady=(4, 0))
        self.empty_label = self.label(self.lap_list.inner, "No laps yet.\nPress Lap while running.", 10,
                                      color=t.text_muted, justify="center")
        self._rendered_laps = -1

    @staticmethod
    def _grid_row(master: tk.Misc, bg: str) -> tk.Frame:
        row = tk.Frame(master, bg=bg)
        for column in range(3):
            row.columnconfigure(column, weight=1, uniform="lap")
        return row

    def _lap(self) -> None:
        if self.stopwatch.running:
            self.stopwatch.lap()

    def _reset(self) -> None:
        if not self.stopwatch.running:
            self.stopwatch.reset()

    def _render_laps(self) -> None:
        t = self.theme
        for child in self.lap_list.inner.winfo_children():
            if child is not self.empty_label:
                child.destroy()
        laps = list(self.stopwatch.newest_laps())
        self.lap_count.configure(text=f"{len(laps)} recorded" if laps else "")
        if not laps:
            self.empty_label.pack(pady=40)
            self._rendered_laps = 0
            return
        self.empty_label.pack_forget()
        fastest = self.stopwatch.fastest_lap() if len(laps) > 1 else None
        slowest = self.stopwatch.slowest_lap() if len(laps) > 1 else None
        for index, lap in enumerate(laps):
            row_bg = t.surface if index % 2 else t.surface_alt
            row = self._grid_row(self.lap_list.inner, row_bg)
            row.pack(fill="x", pady=1)
            color = t.text
            tag = ""
            if lap is fastest:
                color, tag = t.success, "  best"
            elif lap is slowest:
                color, tag = t.danger, "  slowest"
            self.label(row, f"{lap.number:02d}{tag}", 10, "bold", color, anchor="w", padx=10, pady=7).grid(
                row=0, column=0, sticky="ew")
            self.label(row, format_duration(lap.split), 10, color=color, family=self.fonts.mono,
                       anchor="e", padx=10).grid(row=0, column=1, sticky="ew")
            self.label(row, format_duration(lap.total), 10, color=t.text_muted, family=self.fonts.mono,
                       anchor="e", padx=10).grid(row=0, column=2, sticky="ew")
            self.lap_list.bind_all_wheel(row)
        self._rendered_laps = len(laps)

    def refresh(self, now: datetime) -> None:
        sw = self.stopwatch
        elapsed = sw.elapsed
        caption = f"LAP {len(sw.laps) + 1}  ·  {format_duration(sw.current_split())}" if elapsed else "READY"
        self.ring.update_ring((elapsed % 60) / 60, format_duration(elapsed), caption)
        self.start_button.set_text("Pause" if sw.running else ("Resume" if elapsed else "Start"))
        self.lap_button.set_enabled(sw.running)
        self.reset_button.set_enabled(not sw.running and elapsed > 0)
        if self._rendered_laps != len(sw.laps):
            self._render_laps()

    def subtitle(self, now: datetime) -> str:
        return "Measure laps with centisecond precision"

    def on_key(self, event: tk.Event) -> bool:
        key = event.keysym.lower()
        if key == "space":
            self.stopwatch.toggle()
        elif key == "l":
            self._lap()
        elif key == "r":
            self._reset()
        else:
            return False
        return True
