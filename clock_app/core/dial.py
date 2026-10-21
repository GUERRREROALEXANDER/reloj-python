"""The clock dial modelled as rings of positions."""

from __future__ import annotations

from dataclasses import dataclass

from ..structures import CircularDoublyLinkedList, RingCursor


@dataclass(frozen=True)
class DialMark:
    """One position on the dial (a minute tick, an hour numeral...)."""

    index: int
    total: int

    @property
    def angle(self) -> float:
        """Angle in degrees measured clockwise from 12 o'clock."""
        return self.index * 360.0 / self.total

    @property
    def is_major(self) -> bool:
        """True for the twelve hour positions."""
        return self.index % (self.total // 12) == 0 if self.total >= 12 else True


class DialRing:
    """A ring of ``size`` dial marks stored in a circular doubly linked list.

    Going from 59 to 0 is just following ``next``; no modulo is needed.
    """

    def __init__(self, size: int) -> None:
        if size <= 0:
            raise ValueError("dial size must be positive")
        self.size = size
        self.marks: CircularDoublyLinkedList[DialMark] = CircularDoublyLinkedList(
            DialMark(i, size) for i in range(size)
        )

    def cursor(self) -> RingCursor[DialMark]:
        return RingCursor(self.marks)

    def __iter__(self):
        return iter(self.marks)

    def __len__(self) -> int:
        return self.size
