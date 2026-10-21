"""Colour themes and fonts."""

from __future__ import annotations

import tkinter.font as tkfont
from dataclasses import dataclass

from ..structures import CircularDoublyLinkedList, RingCursor


@dataclass(frozen=True)
class Theme:
    name: str
    dark: bool
    # Application chrome
    background: str
    sidebar: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_text: str
    success: str
    danger: str
    # Clock face
    face_rim: str
    face_outer: str
    face_inner: str
    tick_major: str
    tick_minor: str
    numeral: str
    hour_hand: str
    minute_hand: str
    second_hand: str
    hand_shadow: str
    pin: str


MIDNIGHT = Theme(
    name="Midnight", dark=True,
    background="#0f1222", sidebar="#0b0d1a", surface="#171b30", surface_alt="#1f2440",
    border="#2a3052", text="#e8eaf6", text_muted="#8b91b5",
    accent="#8b5cf6", accent_hover="#a07bff", accent_text="#ffffff",
    success="#34d399", danger="#f87171",
    face_rim="#2c3258", face_outer="#1a1e38", face_inner="#20254a",
    tick_major="#e8eaf6", tick_minor="#4a517e", numeral="#c9cdf0",
    hour_hand="#e8eaf6", minute_hand="#e8eaf6", second_hand="#ff7a45",
    hand_shadow="#0a0c18", pin="#ff7a45",
)

DAYLIGHT = Theme(
    name="Daylight", dark=False,
    background="#f3f5fb", sidebar="#ffffff", surface="#ffffff", surface_alt="#eef1f8",
    border="#dde2ef", text="#1e2a5a", text_muted="#6b7394",
    accent="#8e2a9c", accent_hover="#a43bb3", accent_text="#ffffff",
    success="#16a34a", danger="#dc2626",
    face_rim="#d5dbea", face_outer="#ffffff", face_inner="#fbfcff",
    tick_major="#1e2a5a", tick_minor="#a9b1cc", numeral="#1e2a5a",
    hour_hand="#1e2a5a", minute_hand="#1e2a5a", second_hand="#ff6b35",
    hand_shadow="#cfd5e6", pin="#ff6b35",
)

AURORA = Theme(
    name="Aurora", dark=True,
    background="#07161a", sidebar="#051013", surface="#0d2228", surface_alt="#123039",
    border="#1c4350", text="#e3fbf7", text_muted="#7fb3ad",
    accent="#2dd4bf", accent_hover="#5eead4", accent_text="#05201c",
    success="#4ade80", danger="#fb7185",
    face_rim="#1a4a52", face_outer="#0c262c", face_inner="#103038",
    tick_major="#e3fbf7", tick_minor="#2f6b72", numeral="#bdeee6",
    hour_hand="#e3fbf7", minute_hand="#e3fbf7", second_hand="#f472b6",
    hand_shadow="#031013", pin="#f472b6",
)

EMBER = Theme(
    name="Ember", dark=True,
    background="#16100d", sidebar="#100b09", surface="#211814", surface_alt="#2b201a",
    border="#3d2d24", text="#fbefe6", text_muted="#b09583",
    accent="#ff6b35", accent_hover="#ff8a5c", accent_text="#1a0d06",
    success="#a3e635", danger="#f87171",
    face_rim="#4a3328", face_outer="#241a15", face_inner="#2c201a",
    tick_major="#fbefe6", tick_minor="#6b5143", numeral="#f1d9c8",
    hour_hand="#fbefe6", minute_hand="#fbefe6", second_hand="#ff6b35",
    hand_shadow="#0d0806", pin="#ff6b35",
)


class ThemeCarousel:
    """Themes arranged in a circular doubly linked list.

    The theme button simply moves the cursor forward; after the last theme it
    comes back to the first one.
    """

    def __init__(self, themes: tuple[Theme, ...] = (MIDNIGHT, DAYLIGHT, AURORA, EMBER)) -> None:
        self.themes: CircularDoublyLinkedList[Theme] = CircularDoublyLinkedList(themes)
        self._cursor = RingCursor(self.themes)

    @property
    def current(self) -> Theme:
        return self._cursor.value

    def next(self) -> Theme:
        return self._cursor.forward()

    def previous(self) -> Theme:
        return self._cursor.backward()

    def peek_next(self) -> Theme:
        node = self._cursor.node
        assert node is not None
        return node.next.value


def blend(color_a: str, color_b: str, amount: float) -> str:
    """Mix two ``#rrggbb`` colours; ``amount`` 0 gives ``a`` and 1 gives ``b``."""
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(x + (y - x) * amount) for x, y in zip(a, b)]
    return "#{:02x}{:02x}{:02x}".format(*mixed)


class Fonts:
    """Picks the best installed font families once Tk is running."""

    def __init__(self) -> None:
        families = set(tkfont.families())

        def pick(*candidates: str) -> str:
            for name in candidates:
                if name in families:
                    return name
            return "TkDefaultFont"

        self.ui = pick("Segoe UI Variable Text", "Segoe UI", "Helvetica Neue", "Arial")
        self.display = pick("Segoe UI Variable Display", "Segoe UI", "Helvetica Neue", "Arial")
        self.light = pick("Segoe UI Variable Display Light", "Segoe UI Light", self.display)
        self.semibold = pick("Segoe UI Variable Display Semib", "Segoe UI Semibold", self.display)
        self.mono = pick("Cascadia Mono", "Consolas", "Courier New")

    def __call__(self, size: int, weight: str = "normal", family: str | None = None) -> tuple:
        return (family or self.ui, size, weight)
