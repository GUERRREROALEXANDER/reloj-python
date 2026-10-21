"""World clock: a carousel of cities."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterator, Optional

from ..core import FixedOffsetTimeProvider, SystemTimeProvider
from ..structures import CircularDoublyLinkedList, RingCursor
from .base import Feature

CITY_CATALOG: tuple[tuple[str, str, float], ...] = (
    ("Bogotá", "Colombia", -5),
    ("Lima", "Peru", -5),
    ("Mexico City", "Mexico", -6),
    ("New York", "USA", -4),
    ("Los Angeles", "USA", -7),
    ("Buenos Aires", "Argentina", -3),
    ("São Paulo", "Brazil", -3),
    ("Santiago", "Chile", -3),
    ("Caracas", "Venezuela", -4),
    ("Madrid", "Spain", 2),
    ("London", "United Kingdom", 1),
    ("Paris", "France", 2),
    ("Berlin", "Germany", 2),
    ("Moscow", "Russia", 3),
    ("Dubai", "UAE", 4),
    ("New Delhi", "India", 5.5),
    ("Beijing", "China", 8),
    ("Tokyo", "Japan", 9),
    ("Seoul", "South Korea", 9),
    ("Sydney", "Australia", 10),
    ("Auckland", "New Zealand", 13),
    ("Honolulu", "USA", -10),
)

DEFAULT_CITIES = ("New York", "Madrid", "London", "Tokyo", "Sydney")


def city_from_catalog(name: str) -> FixedOffsetTimeProvider:
    for city, country, offset in CITY_CATALOG:
        if city == name:
            return FixedOffsetTimeProvider(city, offset, country)
    raise KeyError(name)


class WorldClock(Feature):
    """Cities stored in a circular doubly linked list with a selection cursor.

    The previous / next buttons of the view move the cursor, wrapping from
    the last city to the first and vice versa.
    """

    def __init__(self, cities: tuple[str, ...] = DEFAULT_CITIES) -> None:
        super().__init__("World")
        self.local = SystemTimeProvider()
        # Keep the ring sorted by UTC offset from the start, so that
        # add_city (which relies on insert_sorted) preserves the order.
        self.cities: CircularDoublyLinkedList[FixedOffsetTimeProvider] = CircularDoublyLinkedList()
        for name in cities:
            self.cities.insert_sorted(city_from_catalog(name), key=lambda c: c.utc_offset())
        self.cursor = RingCursor(self.cities)

    @property
    def selected(self) -> Optional[FixedOffsetTimeProvider]:
        return self.cursor.node.value if self.cursor.node else None

    def next_city(self) -> Optional[FixedOffsetTimeProvider]:
        if self.cities:
            self.cursor.forward()
            self.emit("selected", self.selected)
        return self.selected

    def previous_city(self) -> Optional[FixedOffsetTimeProvider]:
        if self.cities:
            self.cursor.backward()
            self.emit("selected", self.selected)
        return self.selected

    def select(self, name: str) -> None:
        if self.cursor.seek(lambda city: city.name == name):
            self.emit("selected", self.selected)

    def add_city(self, name: str) -> bool:
        if any(city.name == name for city in self.cities):
            return False
        city = city_from_catalog(name)
        node = self.cities.insert_sorted(city, key=lambda c: c.utc_offset())
        self.cursor.place(node)
        self.emit("changed")
        return True

    def remove_selected(self) -> Optional[FixedOffsetTimeProvider]:
        removed = self.cursor.detach_current()
        self.emit("changed")
        return removed

    def available_cities(self) -> list[str]:
        taken = {city.name for city in self.cities}
        return [name for name, _, _ in CITY_CATALOG if name not in taken]

    def difference_from_local(self, city: FixedOffsetTimeProvider) -> str:
        delta: timedelta = city.utc_offset() - self.local.utc_offset()
        hours = delta.total_seconds() / 3600
        if hours == 0:
            return "Same time"
        sign = "+" if hours > 0 else "−"
        value = f"{abs(hours):g}"
        return f"{sign}{value} h"

    def __iter__(self) -> Iterator[FixedOffsetTimeProvider]:
        return iter(self.cities)

    def tick(self, now: datetime) -> None:
        pass

    def summary(self) -> str:
        city = self.selected
        if city is None:
            return "No cities"
        return f"{city.name} {city.now():%H:%M}"
