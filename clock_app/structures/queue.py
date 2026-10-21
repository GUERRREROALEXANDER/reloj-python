"""FIFO queue backed by the circular doubly linked list."""

from __future__ import annotations

from typing import Generic, Iterator, TypeVar

from .circular_doubly_linked_list import CircularDoublyLinkedList

T = TypeVar("T")


class LinkedQueue(Generic[T]):
    """Enqueue at the tail, dequeue at the head, both in O(1)."""

    def __init__(self) -> None:
        self._items: CircularDoublyLinkedList[T] = CircularDoublyLinkedList()

    def enqueue(self, value: T) -> None:
        self._items.append(value)

    def dequeue(self) -> T:
        if self._items.is_empty():
            raise IndexError("dequeue from empty queue")
        return self._items.pop_front()

    def peek(self) -> T:
        if self._items.head is None:
            raise IndexError("peek into empty queue")
        return self._items.head.value

    def is_empty(self) -> bool:
        return self._items.is_empty()

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)
