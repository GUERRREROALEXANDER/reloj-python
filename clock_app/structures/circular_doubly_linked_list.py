"""Generic circular doubly linked list and a cursor that walks over it."""

from __future__ import annotations

from typing import Callable, Generic, Iterable, Iterator, Optional, TypeVar

T = TypeVar("T")


class Node(Generic[T]):
    """A single node that knows its previous and next neighbours."""

    __slots__ = ("value", "next", "prev")

    def __init__(self, value: T) -> None:
        self.value: T = value
        self.next: Node[T] = self
        self.prev: Node[T] = self

    def __repr__(self) -> str:
        return f"Node({self.value!r})"


class CircularDoublyLinkedList(Generic[T]):
    """Circular doubly linked list.

    The last node points forward to the head and the head points back to the
    last node, so traversal in both directions never reaches an end. That
    property is what lets clock hands, carousels and world clocks wrap around
    without any index arithmetic.
    """

    def __init__(self, items: Optional[Iterable[T]] = None) -> None:
        self._head: Optional[Node[T]] = None
        self._size = 0
        for item in items or ():
            self.append(item)

    # ------------------------------------------------------------------ info
    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._size > 0

    def is_empty(self) -> bool:
        return self._size == 0

    @property
    def head(self) -> Optional[Node[T]]:
        return self._head

    @property
    def tail(self) -> Optional[Node[T]]:
        return self._head.prev if self._head else None

    # ------------------------------------------------------------- insertion
    def append(self, value: T) -> Node[T]:
        """Insert at the end (just before the head)."""
        node = Node(value)
        if self._head is None:
            self._head = node
        else:
            self._link_after(self._head.prev, node)
        self._size += 1
        return node

    def prepend(self, value: T) -> Node[T]:
        """Insert at the beginning and make the new node the head."""
        node = self.append(value)
        self._head = node
        return node

    def insert_after(self, anchor: Node[T], value: T) -> Node[T]:
        node = Node(value)
        self._link_after(anchor, node)
        self._size += 1
        return node

    def insert_before(self, anchor: Node[T], value: T) -> Node[T]:
        node = self.insert_after(anchor.prev, value)
        if anchor is self._head:
            self._head = node
        return node

    def insert_sorted(self, value: T, key: Callable[[T], object] = lambda v: v) -> Node[T]:
        """Insert keeping the list ordered by ``key`` (ascending)."""
        if self._head is None or key(value) < key(self._head.value):  # type: ignore[operator]
            return self.prepend(value)
        current = self._head
        while current.next is not self._head and key(current.next.value) <= key(value):  # type: ignore[operator]
            current = current.next
        return self.insert_after(current, value)

    # --------------------------------------------------------------- removal
    def remove_node(self, node: Node[T]) -> T:
        if self._head is None:
            raise IndexError("remove from empty list")
        if self._size == 1:
            self._head = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            if node is self._head:
                self._head = node.next
        node.next = node.prev = node
        self._size -= 1
        return node.value

    def remove(self, value: T) -> bool:
        node = self.find(lambda v: v == value)
        if node is None:
            return False
        self.remove_node(node)
        return True

    def pop_front(self) -> T:
        if self._head is None:
            raise IndexError("pop from empty list")
        return self.remove_node(self._head)

    def pop_back(self) -> T:
        if self._head is None:
            raise IndexError("pop from empty list")
        return self.remove_node(self._head.prev)

    def clear(self) -> None:
        self._head = None
        self._size = 0

    # ----------------------------------------------------------- navigation
    def find(self, predicate: Callable[[T], bool]) -> Optional[Node[T]]:
        for node in self.nodes():
            if predicate(node.value):
                return node
        return None

    def node_at(self, index: int) -> Node[T]:
        """Return the node at ``index``; indexes wrap around the circle."""
        if self._head is None:
            raise IndexError("index into empty list")
        index %= self._size
        # Walk in whichever direction is shorter.
        if index <= self._size // 2:
            node = self._head
            for _ in range(index):
                node = node.next
        else:
            node = self._head
            for _ in range(self._size - index):
                node = node.prev
        return node

    def __getitem__(self, index: int) -> T:
        return self.node_at(index).value

    def rotate(self, steps: int = 1) -> None:
        """Move the head ``steps`` positions forward (negative = backward)."""
        if self._head is None:
            return
        self._head = self.node_at(steps)

    # ------------------------------------------------------------ iteration
    def nodes(self) -> Iterator[Node[T]]:
        if self._head is None:
            return
        node = self._head
        for _ in range(self._size):
            yield node
            node = node.next

    def __iter__(self) -> Iterator[T]:
        for node in self.nodes():
            yield node.value

    def __reversed__(self) -> Iterator[T]:
        if self._head is None:
            return
        node = self._head.prev
        for _ in range(self._size):
            yield node.value
            node = node.prev

    def __contains__(self, value: object) -> bool:
        return any(v == value for v in self)

    def to_list(self) -> list[T]:
        return list(self)

    def __repr__(self) -> str:
        return f"CircularDoublyLinkedList({self.to_list()!r})"

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _link_after(anchor: Node[T], node: Node[T]) -> None:
        node.prev = anchor
        node.next = anchor.next
        anchor.next.prev = node
        anchor.next = node


class RingCursor(Generic[T]):
    """A movable pointer over a :class:`CircularDoublyLinkedList`."""

    def __init__(self, ring: CircularDoublyLinkedList[T]) -> None:
        self._ring = ring
        self._node: Optional[Node[T]] = ring.head

    @property
    def ring(self) -> CircularDoublyLinkedList[T]:
        return self._ring

    @property
    def node(self) -> Optional[Node[T]]:
        if self._node is None and self._ring.head is not None:
            self._node = self._ring.head
        return self._node

    @property
    def value(self) -> T:
        node = self.node
        if node is None:
            raise IndexError("cursor over empty list")
        return node.value

    def forward(self, steps: int = 1) -> T:
        node = self.node
        if node is None:
            raise IndexError("cursor over empty list")
        for _ in range(steps):
            node = node.next
        self._node = node
        return node.value

    def backward(self, steps: int = 1) -> T:
        node = self.node
        if node is None:
            raise IndexError("cursor over empty list")
        for _ in range(steps):
            node = node.prev
        self._node = node
        return node.value

    def place(self, node: Node[T]) -> None:
        self._node = node

    def seek(self, predicate: Callable[[T], bool]) -> bool:
        """Move to the nearest node matching ``predicate``.

        Both directions are explored at the same time, so the cursor reaches
        the target in at most ``len(ring) // 2`` steps.
        """
        start = self.node
        if start is None:
            return False
        if predicate(start.value):
            return True
        ahead, behind = start.next, start.prev
        for _ in range(len(self._ring) // 2 + 1):
            if predicate(ahead.value):
                self._node = ahead
                return True
            if predicate(behind.value):
                self._node = behind
                return True
            ahead, behind = ahead.next, behind.prev
        return False

    def detach_current(self) -> Optional[T]:
        """Remove the current node and step to its successor."""
        node = self.node
        if node is None:
            return None
        successor = node.next if len(self._ring) > 1 else None
        value = self._ring.remove_node(node)
        self._node = successor
        return value
