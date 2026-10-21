"""Drives the three hands from a time provider."""

from __future__ import annotations

from datetime import datetime

from .hands import Hand, HourHand, MinuteHand, SecondHand
from .time_provider import SystemTimeProvider, TimeProvider


class ClockEngine:
    """Keeps a set of hands synchronised with a :class:`TimeProvider`."""

    def __init__(self, provider: TimeProvider | None = None, smooth_seconds: bool = True) -> None:
        self.provider = provider or SystemTimeProvider()
        self.hour_hand = HourHand()
        self.minute_hand = MinuteHand()
        self.second_hand = SecondHand(smooth_seconds)
        self.moment: datetime = self.provider.now()
        self.tick()

    @property
    def hands(self) -> tuple[Hand, ...]:
        """Hands ordered from back to front, the drawing order."""
        return self.hour_hand, self.minute_hand, self.second_hand

    @property
    def smooth_seconds(self) -> bool:
        return self.second_hand.smooth

    @smooth_seconds.setter
    def smooth_seconds(self, value: bool) -> None:
        self.second_hand.smooth = value

    def use_provider(self, provider: TimeProvider) -> None:
        self.provider = provider
        self.tick()

    def tick(self) -> datetime:
        self.moment = self.provider.now()
        for hand in self.hands:
            hand.update(self.moment)
        return self.moment
