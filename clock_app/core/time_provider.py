"""Sources of the current time.

Every provider exposes the same ``now()`` method, so the clock engine and the
views can work with the local machine time or with any city of the world
without knowing which one they hold.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone


class TimeProvider(ABC):
    """Abstract source of time."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def now(self) -> datetime:
        """Return the current moment as an aware datetime."""

    @abstractmethod
    def utc_offset(self) -> timedelta:
        """Return the offset from UTC for the current moment."""

    def offset_label(self) -> str:
        total_minutes = int(self.utc_offset().total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        hours, minutes = divmod(abs(total_minutes), 60)
        return f"UTC{sign}{hours:02d}:{minutes:02d}"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r})"


class SystemTimeProvider(TimeProvider):
    """The time configured on this computer."""

    def __init__(self, name: str = "Local") -> None:
        super().__init__(name)

    def now(self) -> datetime:
        return datetime.now().astimezone()

    def utc_offset(self) -> timedelta:
        return self.now().utcoffset() or timedelta(0)


class FixedOffsetTimeProvider(TimeProvider):
    """A city with a fixed offset from UTC.

    Fixed offsets keep the app dependency-free (Windows ships without the
    IANA time-zone database), at the cost of ignoring daylight saving time.
    """

    def __init__(self, name: str, offset_hours: float, country: str = "") -> None:
        super().__init__(name)
        self.country = country
        self._offset = timedelta(hours=offset_hours)
        self._zone = timezone(self._offset, name)

    def now(self) -> datetime:
        return datetime.now(timezone.utc).astimezone(self._zone)

    def utc_offset(self) -> timedelta:
        return self._offset

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FixedOffsetTimeProvider) and other.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)
