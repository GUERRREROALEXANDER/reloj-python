"""Alarms ordered by time of day."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, Optional

from ..structures import CircularDoublyLinkedList, LinkedQueue
from .base import Feature

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@dataclass
class Alarm:
    hour: int
    minute: int
    label: str = "Alarm"
    enabled: bool = True
    days: frozenset[int] = frozenset()  # weekdays 0..6; empty = every day
    id: int = field(default_factory=itertools.count(1).__next__)
    snoozed_until: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not (0 <= self.hour < 24 and 0 <= self.minute < 60):
            raise ValueError("invalid alarm time")

    @property
    def minutes_of_day(self) -> int:
        return self.hour * 60 + self.minute

    def time_text(self, use_24h: bool = True) -> str:
        if use_24h:
            return f"{self.hour:02d}:{self.minute:02d}"
        suffix = "AM" if self.hour < 12 else "PM"
        return f"{(self.hour % 12) or 12}:{self.minute:02d} {suffix}"

    def days_text(self) -> str:
        if not self.days or len(self.days) == 7:
            return "Every day"
        if self.days == frozenset(range(5)):
            return "Weekdays"
        if self.days == frozenset({5, 6}):
            return "Weekends"
        return " ".join(WEEKDAY_NAMES[d] for d in sorted(self.days))

    def rings_on(self, weekday: int) -> bool:
        return not self.days or weekday in self.days

    def next_occurrence(self, now: datetime) -> datetime:
        candidate = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        for _ in range(7):
            if self.rings_on(candidate.weekday()):
                break
            candidate += timedelta(days=1)
        return candidate


class AlarmManager(Feature):
    """Keeps alarms in a circular doubly linked list sorted by time of day.

    Because the list is circular, "the next alarm after now" is found by
    walking forward from the first alarm later than now, wrapping past
    midnight back to the earliest one.
    """

    SNOOZE_MINUTES = 5

    def __init__(self) -> None:
        super().__init__("Alarms")
        self.alarms: CircularDoublyLinkedList[Alarm] = CircularDoublyLinkedList()
        self.pending: LinkedQueue[Alarm] = LinkedQueue()
        self._last_fired: dict[int, str] = {}

    def add(self, hour: int, minute: int, label: str = "Alarm", days: frozenset[int] = frozenset()) -> Alarm:
        alarm = Alarm(hour, minute, label.strip() or "Alarm", days=days)
        self.alarms.insert_sorted(alarm, key=lambda a: a.minutes_of_day)
        self.emit("changed")
        return alarm

    def remove(self, alarm_id: int) -> bool:
        node = self.alarms.find(lambda a: a.id == alarm_id)
        if node is None:
            return False
        self.alarms.remove_node(node)
        self._last_fired.pop(alarm_id, None)
        self.emit("changed")
        return True

    def toggle(self, alarm_id: int) -> Optional[Alarm]:
        node = self.alarms.find(lambda a: a.id == alarm_id)
        if node is None:
            return None
        node.value.enabled = not node.value.enabled
        node.value.snoozed_until = None
        self.emit("changed")
        return node.value

    def snooze(self, alarm: Alarm, now: datetime) -> None:
        alarm.snoozed_until = now.replace(second=0, microsecond=0) + timedelta(minutes=self.SNOOZE_MINUTES)
        self.emit("changed")

    def dismiss(self, alarm: Alarm) -> None:
        alarm.snoozed_until = None
        self.emit("changed")

    def __iter__(self) -> Iterator[Alarm]:
        return iter(self.alarms)

    def __len__(self) -> int:
        return len(self.alarms)

    def next_alarm(self, now: datetime) -> Optional[tuple[Alarm, datetime]]:
        enabled = [a for a in self.alarms if a.enabled]
        if not enabled:
            return None
        upcoming = []
        for alarm in enabled:
            when = alarm.snoozed_until or alarm.next_occurrence(now)
            upcoming.append((when, alarm))
        when, alarm = min(upcoming, key=lambda pair: pair[0])
        return alarm, when

    def tick(self, now: datetime) -> None:
        stamp = now.strftime("%Y-%m-%d %H:%M")
        for alarm in self.alarms:
            if not alarm.enabled or self._last_fired.get(alarm.id) == stamp:
                continue
            due_snooze = alarm.snoozed_until is not None and now >= alarm.snoozed_until
            due_regular = (
                alarm.snoozed_until is None
                and now.hour == alarm.hour
                and now.minute == alarm.minute
                and alarm.rings_on(now.weekday())
            )
            if due_snooze or due_regular:
                alarm.snoozed_until = None
                self._last_fired[alarm.id] = stamp
                self.pending.enqueue(alarm)
                self.emit("ringing", alarm)

    def summary(self) -> str:
        active = sum(1 for a in self.alarms if a.enabled)
        if not self.alarms:
            return "No alarms"
        return f"{active} of {len(self.alarms)} active"
