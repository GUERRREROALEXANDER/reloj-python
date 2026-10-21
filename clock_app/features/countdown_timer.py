"""Countdown timer with presets."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable, Optional

from ..structures import CircularDoublyLinkedList, RingCursor
from .base import Feature, format_duration

DEFAULT_PRESETS = (60, 3 * 60, 5 * 60, 10 * 60, 15 * 60, 25 * 60, 45 * 60, 60 * 60)


class CountdownTimer(Feature):
    """Counts down from a duration and emits ``finished`` at zero.

    Presets form a ring so the user can cycle through them with next/previous
    buttons, wrapping from the last preset back to the first.
    """

    def __init__(self, duration: float = 5 * 60, clock: Callable[[], float] = time.monotonic) -> None:
        super().__init__("Timer")
        self._clock = clock
        self.duration = float(duration)
        self._remaining = float(duration)
        self._deadline: Optional[float] = None
        self.finished = False
        self.presets: CircularDoublyLinkedList[int] = CircularDoublyLinkedList(DEFAULT_PRESETS)
        self.preset_cursor = RingCursor(self.presets)
        self.preset_cursor.seek(lambda seconds: seconds == int(duration))

    @property
    def running(self) -> bool:
        return self._deadline is not None

    @property
    def remaining(self) -> float:
        if self._deadline is None:
            return self._remaining
        return max(0.0, self._deadline - self._clock())

    @property
    def progress(self) -> float:
        """Fraction of the duration already consumed, 0..1."""
        if self.duration <= 0:
            return 0.0
        return 1.0 - self.remaining / self.duration

    def set_duration(self, seconds: float) -> None:
        self.duration = max(1.0, float(seconds))
        self._remaining = self.duration
        self._deadline = None
        self.finished = False
        self.emit("changed", self.duration)

    def next_preset(self) -> int:
        seconds = self.preset_cursor.forward()
        self.set_duration(seconds)
        return seconds

    def previous_preset(self) -> int:
        seconds = self.preset_cursor.backward()
        self.set_duration(seconds)
        return seconds

    def start(self) -> None:
        if self.running:
            return
        if self.finished or self._remaining <= 0:
            self._remaining = self.duration
            self.finished = False
        self._deadline = self._clock() + self._remaining
        self.emit("started")

    def pause(self) -> None:
        if self._deadline is not None:
            self._remaining = self.remaining
            self._deadline = None
            self.emit("paused")

    def toggle(self) -> None:
        self.pause() if self.running else self.start()

    def reset(self) -> None:
        self._remaining = self.duration
        self._deadline = None
        self.finished = False
        self.emit("reset")

    def add_time(self, seconds: float) -> None:
        if self._deadline is not None:
            self._deadline += seconds
        else:
            self._remaining += seconds
        self.duration += seconds
        self.finished = False

    def tick(self, now: datetime) -> None:
        if self._deadline is not None and self.remaining <= 0:
            self._deadline = None
            self._remaining = 0.0
            self.finished = True
            self.emit("finished")

    def summary(self) -> str:
        if self.finished:
            return "Time's up!"
        if self.running:
            return f"{format_duration(self.remaining, show_centis=False)} left"
        if self._remaining < self.duration:
            return f"Paused · {format_duration(self._remaining, show_centis=False)}"
        return f"Set to {format_duration(self.duration, show_centis=False)}"
