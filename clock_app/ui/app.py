"""Main application window."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from ..core import ClockEngine
from ..features import AlarmManager, CountdownTimer, Feature, Stopwatch, WorldClock
from ..structures import CircularDoublyLinkedList, RingCursor
from .analog_clock import DialStyleCarousel
from .icons import ICONS
from .notification import RingingDialog
from .theme import Fonts, Theme, ThemeCarousel, blend
from .views import AlarmView, ClockView, StopwatchView, TimerView, View, WorldView
from .widgets import draw_rounded_rect

FRAME_MS = 33          # ~30 frames per second
SIDEBAR_WIDTH = 248

VIEW_CLASSES: tuple[type[View], ...] = (ClockView, WorldView, AlarmView, StopwatchView, TimerView)


class ClockApp(tk.Tk):
    """Owns the backend objects and swaps the views in the main area.

    The backend lives here, not in the views, so the whole interface can be
    rebuilt (for example when the theme changes) without losing any state.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tk.call("tk", "scaling", 96 / 72)
        self.title("Chronos · Python Clock")
        self.geometry(self._centered_geometry(1280, 800))
        self.minsize(1120, 720)

        self.fonts = Fonts()
        self.themes = ThemeCarousel()
        self.dial_styles = DialStyleCarousel()
        self.settings = {"use_24h": True}

        # Backend
        self.engine = ClockEngine()
        self.stopwatch = Stopwatch()
        self.timer = CountdownTimer()
        self.alarms = AlarmManager()
        self.world = WorldClock()
        self.features: tuple[Feature, ...] = (self.stopwatch, self.timer, self.alarms, self.world)
        self.timer.subscribe(self._on_timer_event)

        # Screens form a ring too: Tab / Shift+Tab walk around it.
        self.views: CircularDoublyLinkedList[type[View]] = CircularDoublyLinkedList(VIEW_CLASSES)
        self.view_cursor = RingCursor(self.views)
        self.current_view: View | None = None
        self._dialog: RingingDialog | None = None
        self._frame = 0

        self.bind_all("<Key>", self._on_key)
        self.bind("<Tab>", lambda _e: self._cycle_view(1))
        self.bind("<Shift-Tab>", lambda _e: self._cycle_view(-1))
        self.bind("<F11>", lambda _e: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Escape>", lambda _e: self.attributes("-fullscreen", False))

        self._build_ui()
        self.after(FRAME_MS, self._loop)

    @property
    def theme(self) -> Theme:
        return self.themes.current

    def _centered_geometry(self, width: int, height: int) -> str:
        width = min(width, self.winfo_screenwidth() - 80)
        height = min(height, self.winfo_screenheight() - 120)
        x = (self.winfo_screenwidth() - width) // 2
        y = max(0, (self.winfo_screenheight() - height) // 2 - 30)
        return f"{width}x{height}+{x}+{y}"

    # ================================================================= build
    def _build_ui(self) -> None:
        for child in self.winfo_children():
            if not isinstance(child, tk.Toplevel):
                child.destroy()
        t = self.theme
        self.configure(bg=t.background)
        self._style_ttk(t)

        self.sidebar = Sidebar(self)
        self.sidebar.pack(side="left", fill="y")

        main = tk.Frame(self, bg=t.background)
        main.pack(side="left", fill="both", expand=True, padx=36, pady=(28, 28))
        header = tk.Frame(main, bg=t.background)
        header.pack(fill="x", pady=(0, 18))
        self.header_title = tk.Label(header, text="", bg=t.background, fg=t.text,
                                     font=self.fonts(26, "bold", self.fonts.semibold))
        self.header_title.pack(anchor="w")
        self.header_subtitle = tk.Label(header, text="", bg=t.background, fg=t.text_muted, font=self.fonts(11))
        self.header_subtitle.pack(anchor="w")
        self.content = tk.Frame(main, bg=t.background)
        self.content.pack(fill="both", expand=True)

        self.current_view = None
        self.show_view(self.view_cursor.value)

    def _style_ttk(self, t: Theme) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Clock.TCombobox", fieldbackground=t.surface_alt, background=t.surface_alt, foreground=t.text,
            arrowcolor=t.text_muted, bordercolor=t.border, lightcolor=t.surface_alt, darkcolor=t.surface_alt,
            padding=6,
        )
        style.map("Clock.TCombobox", fieldbackground=[("readonly", t.surface_alt)],
                  foreground=[("readonly", t.text)], selectbackground=[("readonly", t.surface_alt)],
                  selectforeground=[("readonly", t.text)], bordercolor=[("focus", t.accent)])
        self.option_add("*TCombobox*Listbox.background", t.surface)
        self.option_add("*TCombobox*Listbox.foreground", t.text)
        self.option_add("*TCombobox*Listbox.selectBackground", t.accent)
        self.option_add("*TCombobox*Listbox.selectForeground", t.accent_text)
        self.option_add("*TCombobox*Listbox.font", self.fonts(11))
        self.option_add("*TCombobox*Listbox.relief", "flat")

    # ============================================================ navigation
    def show_view(self, view_class: type[View]) -> None:
        if self.current_view is not None:
            if isinstance(self.current_view, view_class):
                return
            self.current_view.destroy()
        self.view_cursor.seek(lambda cls: cls is view_class)
        view = view_class(self.content, self)
        view.pack(fill="both", expand=True)
        view.on_show()
        self.current_view = view
        self.header_title.configure(text=view_class.title)
        self.sidebar.set_active(view_class)
        self._refresh_frame(force_header=True)

    def _cycle_view(self, direction: int) -> str:
        view_class = self.view_cursor.forward() if direction > 0 else self.view_cursor.backward()
        self.show_view(view_class)
        return "break"

    def next_theme(self) -> None:
        self.themes.next()
        self._build_ui()

    def _on_key(self, event: tk.Event) -> None:
        if isinstance(event.widget, (tk.Entry, ttk.Combobox)):
            return
        if event.char and event.char in "12345":
            self.show_view(VIEW_CLASSES[int(event.char) - 1])
        elif event.keysym.lower() == "t" and not (event.state & 0x4):
            self.next_theme()
        elif self.current_view is not None:
            self.current_view.on_key(event)

    # ================================================================== loop
    def _loop(self) -> None:
        try:
            self._refresh_frame()
        finally:
            self.after(FRAME_MS, self._loop)

    def _refresh_frame(self, force_header: bool = False) -> None:
        now = self.engine.tick()
        local = now.replace(tzinfo=None)
        for feature in self.features:
            feature.tick(local)
        if self.current_view is not None:
            self.current_view.refresh(now)
        self._frame += 1
        if force_header or self._frame % 15 == 0:
            if self.current_view is not None:
                self.header_subtitle.configure(text=self.current_view.subtitle(now))
            self.sidebar.refresh(now)
        self._show_pending_alarm()

    # ========================================================= notifications
    def _show_pending_alarm(self) -> None:
        if self._dialog is not None or self.alarms.pending.is_empty():
            return
        alarm = self.alarms.pending.dequeue()
        time_text = alarm.time_text(self.settings["use_24h"])
        self._open_dialog(
            alarm.label, f"It's {time_text}  ·  {alarm.days_text()}",
            on_dismiss=lambda: self.alarms.dismiss(alarm),
            on_snooze=lambda: self.alarms.snooze(alarm, datetime.now()),
        )

    def _on_timer_event(self, event: str, _payload) -> None:
        if event == "finished":
            def restart() -> None:
                self.timer.reset()
                self.timer.start()
            self._open_dialog("Time's up!", "Your countdown has reached zero.",
                              on_dismiss=self.timer.reset, on_snooze=restart, snooze_text="Restart")

    def _open_dialog(self, title, message, on_dismiss, on_snooze=None, snooze_text="Snooze 5 min") -> None:
        if self._dialog is not None:
            self._dialog.chime.stop()
            self._dialog.destroy()

        def finish(callback):
            def run() -> None:
                self._dialog = None
                callback()
            return run

        self.deiconify()
        self.lift()
        self._dialog = RingingDialog(
            self, self.theme, self.fonts, title, message, finish(on_dismiss),
            finish(on_snooze) if on_snooze else None, snooze_text,
        )


class Sidebar(tk.Canvas):
    """Navigation rail drawn on a single canvas."""

    ITEM_HEIGHT = 62
    TOP = 128

    def __init__(self, app: ClockApp) -> None:
        t = app.theme
        super().__init__(app, width=SIDEBAR_WIDTH, bg=t.sidebar, highlightthickness=0, bd=0)
        self.app = app
        self.theme = t
        self.active: type[View] | None = None
        self._hover: int | None = None
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", lambda _e: self._set_hover(None))
        self.bind("<Button-1>", self._on_click)

    def _features_for(self, view_class: type[View]):
        return {
            ClockView: None, WorldView: self.app.world, AlarmView: self.app.alarms,
            StopwatchView: self.app.stopwatch, TimerView: self.app.timer,
        }[view_class]

    def _draw(self) -> None:
        self.delete("all")
        t, fonts = self.theme, self.app.fonts
        w, h = self.winfo_width(), self.winfo_height()
        self.create_line(w - 1, 0, w - 1, h, fill=blend(t.sidebar, t.border, 0.7))

        # Brand
        self.create_oval(26, 34, 70, 78, fill=t.accent, outline=t.accent)
        ICONS["clock"].draw(self, 48, 56, 24, t.accent_text, 2.5)
        self.create_text(84, 44, text="Chronos", anchor="w", fill=t.text, font=fonts(17, "bold", fonts.semibold))
        self.create_text(85, 68, text="PYTHON CLOCK", anchor="w", fill=t.text_muted, font=fonts(8, "bold"))

        self.create_text(28, self.TOP - 18, text="MENU", anchor="w", fill=t.text_muted, font=fonts(8, "bold"))
        for index, view_class in enumerate(VIEW_CLASSES):
            self._draw_item(index, view_class)

        # Theme switcher at the bottom.
        y = h - 88
        hovered = self._hover == -1
        fill = blend(t.sidebar, t.text, 0.08 if hovered else 0.04)
        draw_rounded_rect(self, 16, y, w - 16, y + 56, 14, fill=fill, outline=blend(t.sidebar, t.border, 0.8))
        ICONS["theme"].draw(self, 42, y + 28, 18, t.accent, 2)
        self.create_text(62, y + 19, text=f"Theme · {t.name}", anchor="w", fill=t.text,
                         font=fonts(10, "bold", fonts.semibold))
        self.create_text(62, y + 38, text=f"Press T  ·  next: {self.app.themes.peek_next().name}", anchor="w",
                         fill=t.text_muted, font=fonts(8))
        self.create_text(w / 2, h - 18, text="1–5 views  ·  Tab cycle  ·  F11 fullscreen", fill=blend(t.sidebar, t.text_muted, 0.7),
                         font=fonts(8))

    def _draw_item(self, index: int, view_class: type[View]) -> None:
        t, fonts = self.theme, self.app.fonts
        w = int(self["width"])
        y = self.TOP + index * self.ITEM_HEIGHT
        active = view_class is self.active
        hovered = self._hover == index
        if active:
            draw_rounded_rect(self, 14, y + 4, w - 14, y + self.ITEM_HEIGHT - 4, 14,
                              fill=blend(t.sidebar, t.accent, 0.16), outline="")
            self.create_line(15, y + 20, 15, y + self.ITEM_HEIGHT - 20, fill=t.accent, width=4, capstyle="round")
        elif hovered:
            draw_rounded_rect(self, 14, y + 4, w - 14, y + self.ITEM_HEIGHT - 4, 14,
                              fill=blend(t.sidebar, t.text, 0.05), outline="")
        color = t.accent if active else (t.text if hovered else t.text_muted)
        ICONS[view_class.icon].draw(self, 44, y + self.ITEM_HEIGHT / 2, 20, color, 2)
        self.create_text(70, y + 22, text=view_class.title, anchor="w",
                         fill=t.text if active or hovered else blend(t.text, t.text_muted, 0.4),
                         font=fonts(11, "bold", fonts.semibold))
        self.create_text(70, y + 42, text="", anchor="w", fill=t.text_muted, font=fonts(8),
                         tags=f"summary{index}")
        self.create_text(w - 30, y + self.ITEM_HEIGHT / 2, text=view_class.shortcut, fill=blend(t.sidebar, t.text_muted, 0.6),
                         font=fonts(8, "bold"))
        self._update_summary(index, view_class)

    def _update_summary(self, index: int, view_class: type[View]) -> None:
        feature = self._features_for(view_class)
        if feature is None:
            text = self.app.engine.moment.strftime("%H:%M:%S" if self.app.settings["use_24h"] else "%I:%M:%S %p")
        else:
            text = feature.summary()
        self.itemconfigure(f"summary{index}", text=text)

    def refresh(self, _now: datetime) -> None:
        for index, view_class in enumerate(VIEW_CLASSES):
            self._update_summary(index, view_class)

    def set_active(self, view_class: type[View]) -> None:
        self.active = view_class
        self._draw()

    def _hit(self, x: int, y: int) -> int | None:
        h = self.winfo_height()
        if h - 88 <= y <= h - 32 and 16 <= x <= SIDEBAR_WIDTH - 16:
            return -1
        index = (y - self.TOP) // self.ITEM_HEIGHT
        if y >= self.TOP and 0 <= index < len(VIEW_CLASSES):
            return int(index)
        return None

    def _on_motion(self, event) -> None:
        self._set_hover(self._hit(event.x, event.y))

    def _set_hover(self, index: int | None) -> None:
        if index != self._hover:
            self._hover = index
            self.configure(cursor="hand2" if index is not None else "")
            self._draw()

    def _on_click(self, event) -> None:
        target = self._hit(event.x, event.y)
        if target == -1:
            self.app.after_idle(self.app.next_theme)
        elif target is not None:
            self.app.show_view(VIEW_CLASSES[target])
