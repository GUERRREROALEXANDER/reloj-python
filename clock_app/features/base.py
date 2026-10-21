"""Common base for every clock feature."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable

Listener = Callable[[str, Any], None]


class Feature(ABC):
    """A feature that is updated on every tick of the application loop.

    Features notify interested parties (normally the views) through simple
    named events, so the backend never imports anything from the UI.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def unsubscribe(self, listener: Listener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit(self, event: str, payload: Any = None) -> None:
        for listener in list(self._listeners):
            listener(event, payload)

    @abstractmethod
    def tick(self, now: datetime) -> None:
        """Advance the feature to ``now``."""

    @abstractmethod
    def summary(self) -> str:
        """One-line, human readable status (shown in the sidebar)."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.summary()!r})"


def format_duration(seconds: float, show_centis: bool = True) -> str:
    """Format a duration as ``HH:MM:SS.cc`` (hours only when needed)."""
    seconds = max(0.0, seconds)
    total_centis = int(seconds * 100)
    centis = total_centis % 100
    total_seconds = total_centis // 100
    hours, rest = divmod(total_seconds, 3600)
    minutes, secs = divmod(rest, 60)
    text = f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"
    return f"{text}.{centis:02d}" if show_centis else text
