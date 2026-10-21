"""World clock screen."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from ...core import ClockEngine
from ..analog_clock import AnalogClock
from ..theme import blend
from ..widgets import Card, RoundedButton, ScrollableFrame
from .base import View


class WorldView(View):
    title = "World"
    icon = "globe"
    shortcut = "2"

    def build(self) -> None:
        t = self.theme
        self.world = self.app.world
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # -------------------------------------------------- featured city
        top = tk.Frame(self, bg=t.background)
        top.grid(row=0, column=0, sticky="nsew")
        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)

        self.featured_engine = ClockEngine(self.world.selected or self.world.local)
        self.featured_clock = AnalogClock(top, t, self.fonts, self.featured_engine, self.app.dial_styles.current)
        self.featured_clock.grid(row=0, column=0, sticky="nsew")
        top.columnconfigure(0, weight=1, minsize=320)

        info = tk.Frame(top, bg=t.background)
        info.grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.country_label = self.label(info, "", 10, "bold", t.accent)
        self.country_label.pack(anchor="w")
        self.city_label = self.label(info, "", 34, "bold", family=self.fonts.semibold)
        self.city_label.pack(anchor="w")
        self.time_label = self.label(info, "", 46, family=self.fonts.light)
        self.time_label.pack(anchor="w")
        self.detail_label = self.label(info, "", 11, color=t.text_muted)
        self.detail_label.pack(anchor="w", pady=(0, 18))

        nav = tk.Frame(info, bg=t.background)
        nav.pack(anchor="w")
        RoundedButton(nav, t, self.fonts, "‹  Previous", self._previous, "secondary", width=130).pack(side="left")
        RoundedButton(nav, t, self.fonts, "Next  ›", self._next, "secondary", width=130).pack(side="left", padx=8)
        RoundedButton(nav, t, self.fonts, "Remove", self._remove, "danger", width=100).pack(side="left")

        add = tk.Frame(info, bg=t.background)
        add.pack(anchor="w", pady=(14, 0))
        self.city_choice = tk.StringVar()
        self.combo = ttk.Combobox(add, textvariable=self.city_choice, state="readonly", width=20,
                                  style="Clock.TCombobox", font=self.fonts(11))
        self.combo.pack(side="left", ipady=4)
        RoundedButton(add, t, self.fonts, "Add city", self._add, "primary", width=120).pack(side="left", padx=8)

        # ------------------------------------------------------ city strip
        self.section_title(self, "All cities  ·  click a clock to focus it").grid(row=1, column=0, sticky="w", pady=(10, 8))
        self.strip = ScrollableHorizontal(self, t.background)
        self.strip.grid(row=2, column=0, sticky="ew")

        self.world.subscribe(self._on_world_event)
        self.bind("<Destroy>", lambda e: self.world.unsubscribe(self._on_world_event) if e.widget is self else None)
        self._render_strip()

    # ---------------------------------------------------------- actions
    def _next(self) -> None:
        self.world.next_city()

    def _previous(self) -> None:
        self.world.previous_city()

    def _remove(self) -> None:
        if len(self.world.cities) > 1:
            self.world.remove_selected()

    def _add(self) -> None:
        name = self.city_choice.get()
        if name in self.world.available_cities() and self.world.add_city(name):
            self.city_choice.set("Choose a city…")

    def _on_world_event(self, event: str, _payload) -> None:
        if event == "changed":
            self._render_strip()
        self._focus_selected()

    def _focus_selected(self) -> None:
        city = self.world.selected
        if city is not None:
            self.featured_engine.use_provider(city)
        for name, card in self.cards.items():
            card.set_selected(city is not None and name == city.name)

    def _render_strip(self) -> None:
        for child in self.strip.inner.winfo_children():
            child.destroy()
        self.cards: dict[str, CityCard] = {}
        for city in self.world:
            card = CityCard(self.strip.inner, self, ClockEngine(city, smooth_seconds=False))
            card.pack(side="left", padx=(0, 12))
            self.cards[city.name] = card
        self.combo.configure(values=self.world.available_cities())
        if self.city_choice.get() not in self.world.available_cities():
            self.city_choice.set("Choose a city…")
        self._focus_selected()

    # ---------------------------------------------------------- refresh
    def refresh(self, now: datetime) -> None:
        self.featured_engine.tick()
        self.featured_clock.refresh()
        city = self.world.selected
        if city is not None:
            moment = self.featured_engine.moment
            self.country_label.configure(text=city.country.upper())
            self.city_label.configure(text=city.name)
            fmt = "%H:%M:%S" if self.app.settings["use_24h"] else "%I:%M:%S %p"
            self.time_label.configure(text=moment.strftime(fmt))
            day_shift = (moment.date() - now.date()).days
            day = {0: "Today", 1: "Tomorrow", -1: "Yesterday"}.get(day_shift, "")
            self.detail_label.configure(
                text=f"{day}, {moment:%d %b}  ·  {city.offset_label()}  ·  {self.world.difference_from_local(city)}")
        for card in self.cards.values():
            card.refresh()

    def subtitle(self, now: datetime) -> str:
        return f"{len(self.world.cities)} cities  ·  your zone {self.world.local.offset_label()}"

    def on_key(self, event: tk.Event) -> bool:
        if event.keysym == "Right":
            self._next()
        elif event.keysym == "Left":
            self._previous()
        else:
            return False
        return True


class CityCard(Card):
    """Small clickable card with a mini analog clock."""

    def __init__(self, master: tk.Misc, view: WorldView, engine: ClockEngine) -> None:
        t = view.theme
        super().__init__(master, t, padding=12, radius=16, width=150, height=196)
        self.view, self.engine = view, engine
        self.selected = False
        self.clock = AnalogClock(self.body, t, view.fonts, engine, compact=True, bg=t.surface, width=126, height=118)
        self.clock.pack()
        self.name_label = view.label(self.body, engine.provider.name, 10, "bold", family=view.fonts.semibold)
        self.name_label.pack(pady=(4, 0))
        self.time_label = view.label(self.body, "", 9, color=t.text_muted)
        self.time_label.pack()
        for widget in (self, self.body, self.clock, self.name_label, self.time_label):
            widget.bind("<Button-1>", self._select)
            widget.configure(cursor="hand2")
            view.strip.bind_all_wheel(widget)

    def _select(self, _event=None) -> None:
        self.view.world.select(self.engine.provider.name)

    def set_selected(self, selected: bool) -> None:
        if selected == self.selected:
            return
        self.selected = selected
        t = self.theme
        self.itemconfigure("shape", outline=t.accent if selected else blend(self.fill, t.border, 0.6),
                           width=2 if selected else 1)

    def _on_resize(self, event) -> None:
        super()._on_resize(event)
        if self.selected:
            self.itemconfigure("shape", outline=self.theme.accent, width=2)

    def refresh(self) -> None:
        self.engine.tick()
        self.clock.refresh()
        fmt = "%H:%M" if self.view.app.settings["use_24h"] else "%I:%M %p"
        self.time_label.configure(
            text=f"{self.engine.moment.strftime(fmt)}  ·  {self.view.world.difference_from_local(self.engine.provider)}")


class ScrollableHorizontal(ScrollableFrame):
    """Horizontal variant of :class:`ScrollableFrame`."""

    def __init__(self, master: tk.Misc, bg: str) -> None:
        super().__init__(master, bg)
        self.canvas.configure(height=200)
        self.canvas.bind("<Configure>", lambda e: None)

    def _on_wheel(self, event) -> None:
        if self.inner.winfo_width() > self.canvas.winfo_width():
            self.canvas.xview_scroll(int(-event.delta / 120), "units")
