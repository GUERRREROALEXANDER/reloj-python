"""Stopwatch with lap history."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterator, Optional

from ..structures import CircularDoublyLinkedList
from .base import Feature, format_duration


@dataclass(frozen=True)
class Lap:
    number: int
    split: float     # duration of this lap
    total: float     # elapsed time when the lap was taken


class Stopwatch(Feature):
    """Start / pause / reset stopwatch.

    Laps live in a circular doubly linked list: appending is O(1) and the
    view walks it backwards to show the newest lap first.
    """

    def __init__(self, clock: Callable[[], float] = time.perf_counter) -> None:
        super().__init__("Stopwatch")
        self._clock = clock
        self._accumulated = 0.0
        self._started_at: Optional[float] = None
        self.laps: CircularDoublyLinkedList[Lap] = CircularDoublyLinkedList()

    @property
    def running(self) -> bool:
        return self._started_at is not None

    @property
    def elapsed(self) -> float:
        if self._started_at is None:
            return self._accumulated
        return self._accumulated + self._clock() - self._started_at

    def start(self) -> None:
        if not self.running:
            self._started_at = self._clock()
            self.emit("started")

    def pause(self) -> None:
        if self._started_at is not None:
            self._accumulated += self._clock() - self._started_at
            self._started_at = None
            self.emit("paused")

    def toggle(self) -> None:
        self.pause() if self.running else self.start()

    def reset(self) -> None:
        self._accumulated = 0.0
        self._started_at = None
        self.laps.clear()
        self.emit("reset")

    def lap(self) -> Optional[Lap]:
        if self.elapsed == 0:
            return None
        total = self.elapsed
        previous = self.laps.tail.value.total if self.laps.tail else 0.0
        lap = Lap(len(self.laps) + 1, total - previous, total)
        self.laps.append(lap)
        self.emit("lap", lap)
        return lap

    def current_split(self) -> float:
        previous = self.laps.tail.value.total if self.laps.tail else 0.0
        return self.elapsed - previous

    def newest_laps(self) -> Iterator[Lap]:
        return reversed(self.laps)

    def fastest_lap(self) -> Optional[Lap]:
        return min(self.laps, key=lambda lap: lap.split, default=None)

    def slowest_lap(self) -> Optional[Lap]:
        return max(self.laps, key=lambda lap: lap.split, default=None)

    def tick(self, now: datetime) -> None:
        # Elapsed time is computed on demand; nothing to advance.
        pass

    def summary(self) -> str:
        if self.elapsed == 0:
            return "Ready"
        state = "Running" if self.running else "Paused"
        return f"{state} · {format_duration(self.elapsed, show_centis=False)}"
