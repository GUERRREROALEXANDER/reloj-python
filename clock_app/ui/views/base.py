"""Base class for every screen of the application."""

from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from ..theme import Fonts, Theme

if TYPE_CHECKING:
    from ..app import ClockApp


class View(tk.Frame, ABC):
    """A screen shown in the main area.

    The application loop calls :meth:`refresh` on the visible view every
    frame without caring which concrete screen it is.
    """

    title: str = ""
    icon: str = ""
    shortcut: str = ""

    def __init__(self, master: tk.Misc, app: "ClockApp") -> None:
        super().__init__(master, bg=app.theme.background)
        self.app = app
        self.build()

    @property
    def theme(self) -> Theme:
        return self.app.theme

    @property
    def fonts(self) -> Fonts:
        return self.app.fonts

    @abstractmethod
    def build(self) -> None:
        """Create the widgets of the view."""

    @abstractmethod
    def refresh(self, now: datetime) -> None:
        """Update the dynamic parts of the view."""

    def subtitle(self, now: datetime) -> str:
        return now.strftime("%A, %d %B %Y")

    def on_show(self) -> None:
        """Called every time the view becomes visible."""

    def on_key(self, event: tk.Event) -> bool:
        """Handle a key press; return True when consumed."""
        return False

    # ------------------------------------------------------------ helpers
    def label(self, master: tk.Misc, text: str = "", size: int = 11, weight: str = "normal",
              color: str | None = None, family: str | None = None, bg: str | None = None, **kwargs) -> tk.Label:
        return tk.Label(
            master, text=text, fg=color or self.theme.text, bg=bg or master["bg"],
            font=self.fonts(size, weight, family), **kwargs,
        )

    def section_title(self, master: tk.Misc, text: str) -> tk.Label:
        return self.label(master, text.upper(), 9, "bold", self.theme.text_muted)
