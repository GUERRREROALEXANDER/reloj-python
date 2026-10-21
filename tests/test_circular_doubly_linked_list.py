"""Tests for CircularDoublyLinkedList, Node and RingCursor."""

import unittest

from clock_app.structures import CircularDoublyLinkedList, Node, RingCursor


def assert_circular(test: unittest.TestCase, ring: CircularDoublyLinkedList) -> None:
    """Check that next/prev links form a consistent circle of len(ring) nodes."""
    if ring.is_empty():
        test.assertIsNone(ring.head)
        test.assertIsNone(ring.tail)
        return
    test.assertIs(ring.tail.next, ring.head)
    test.assertIs(ring.head.prev, ring.tail)
    node = ring.head
    for _ in range(len(ring)):
        test.assertIs(node.next.prev, node)
        test.assertIs(node.prev.next, node)
        node = node.next
    test.assertIs(node, ring.head)


class NodeTests(unittest.TestCase):
    def test_new_node_points_to_itself(self):
        node = Node(5)
        self.assertEqual(node.value, 5)
        self.assertIs(node.next, node)
        self.assertIs(node.prev, node)

    def test_repr(self):
        self.assertEqual(repr(Node("a")), "Node('a')")


class ConstructionTests(unittest.TestCase):
    def test_empty_list(self):
        ring = CircularDoublyLinkedList()
        self.assertEqual(len(ring), 0)
        self.assertFalse(ring)
        self.assertTrue(ring.is_empty())
        self.assertIsNone(ring.head)
        self.assertIsNone(ring.tail)
        self.assertEqual(ring.to_list(), [])
        self.assertEqual(list(reversed(ring)), [])

    def test_from_iterable(self):
        ring = CircularDoublyLinkedList([1, 2, 3])
        self.assertEqual(ring.to_list(), [1, 2, 3])
        self.assertEqual(len(ring), 3)
        self.assertTrue(ring)
        assert_circular(self, ring)

    def test_repr(self):
        self.assertEqual(repr(CircularDoublyLinkedList([1, 2])), "CircularDoublyLinkedList([1, 2])")


class InsertionTests(unittest.TestCase):
    def test_append_single_node_is_its_own_neighbour(self):
        ring = CircularDoublyLinkedList()
        node = ring.append("x")
        self.assertIs(ring.head, node)
        self.assertIs(ring.tail, node)
        self.assertIs(node.next, node)
        self.assertIs(node.prev, node)

    def test_append_adds_at_tail(self):
        ring = CircularDoublyLinkedList()
        for value in "abc":
            ring.append(value)
        self.assertEqual(ring.to_list(), ["a", "b", "c"])
        self.assertEqual(ring.tail.value, "c")
        assert_circular(self, ring)

    def test_prepend_becomes_head(self):
        ring = CircularDoublyLinkedList([2, 3])
        node = ring.prepend(1)
        self.assertIs(ring.head, node)
        self.assertEqual(ring.to_list(), [1, 2, 3])
        self.assertEqual(ring.tail.value, 3)
        assert_circular(self, ring)

    def test_prepend_on_empty(self):
        ring = CircularDoublyLinkedList()
        ring.prepend(1)
        self.assertEqual(ring.to_list(), [1])
        assert_circular(self, ring)

    def test_insert_after_middle(self):
        ring = CircularDoublyLinkedList([1, 3])
        ring.insert_after(ring.head, 2)
        self.assertEqual(ring.to_list(), [1, 2, 3])
        assert_circular(self, ring)

    def test_insert_after_tail_becomes_new_tail(self):
        ring = CircularDoublyLinkedList([1, 2])
        node = ring.insert_after(ring.tail, 3)
        self.assertIs(ring.tail, node)
        self.assertEqual(ring.to_list(), [1, 2, 3])
        assert_circular(self, ring)

    def test_insert_before_head_becomes_new_head(self):
        ring = CircularDoublyLinkedList([2, 3])
        node = ring.insert_before(ring.head, 1)
        self.assertIs(ring.head, node)
        self.assertEqual(ring.to_list(), [1, 2, 3])
        assert_circular(self, ring)

    def test_insert_before_middle(self):
        ring = CircularDoublyLinkedList([1, 3])
        ring.insert_before(ring.tail, 2)
        self.assertEqual(ring.to_list(), [1, 2, 3])
        self.assertEqual(ring.head.value, 1)
        assert_circular(self, ring)

    def test_insert_sorted_keeps_ascending_order(self):
        ring = CircularDoublyLinkedList()
        for value in [5, 1, 4, 2, 3, 0, 6]:
            ring.insert_sorted(value)
        self.assertEqual(ring.to_list(), [0, 1, 2, 3, 4, 5, 6])
        assert_circular(self, ring)

    def test_insert_sorted_with_key(self):
        ring = CircularDoublyLinkedList()
        for word in ["ccc", "a", "bb"]:
            ring.insert_sorted(word, key=len)
        self.assertEqual(ring.to_list(), ["a", "bb", "ccc"])

    def test_insert_sorted_equal_keys_are_stable(self):
        ring = CircularDoublyLinkedList()
        for item in [(1, "first"), (0, "zero"), (1, "second"), (1, "third")]:
            ring.insert_sorted(item, key=lambda pair: pair[0])
        self.assertEqual([tag for _, tag in ring], ["zero", "first", "second", "third"])

    def test_insert_sorted_largest_goes_to_tail(self):
        ring = CircularDoublyLinkedList([1, 2])
        node = ring.insert_sorted(9)
        self.assertIs(ring.tail, node)
        assert_circular(self, ring)


class RemovalTests(unittest.TestCase):
    def test_remove_head(self):
        ring = CircularDoublyLinkedList([1, 2, 3])
        self.assertEqual(ring.remove_node(ring.head), 1)
        self.assertEqual(ring.to_list(), [2, 3])
        self.assertEqual(ring.head.value, 2)
        assert_circular(self, ring)

    def test_remove_tail(self):
        ring = CircularDoublyLinkedList([1, 2, 3])
        self.assertEqual(ring.remove_node(ring.tail), 3)
        self.assertEqual(ring.to_list(), [1, 2])
        self.assertEqual(ring.tail.value, 2)
        assert_circular(self, ring)

    def test_remove_middle(self):
        ring = CircularDoublyLinkedList([1, 2, 3])
        self.assertEqual(ring.remove_node(ring.head.next), 2)
        self.assertEqual(ring.to_list(), [1, 3])
        assert_circular(self, ring)

    def test_remove_single_node_empties_list(self):
        ring = CircularDoublyLinkedList([1])
        self.assertEqual(ring.remove_node(ring.head), 1)
        self.assertTrue(ring.is_empty())
        assert_circular(self, ring)

    def test_removed_node_is_unlinked(self):
        ring = CircularDoublyLinkedList([1, 2, 3])
        node = ring.head.next
        ring.remove_node(node)
        self.assertIs(node.next, node)
        self.assertIs(node.prev, node)

    def test_remove_by_value(self):
        ring = CircularDoublyLinkedList([1, 2, 3, 2])
        self.assertTrue(ring.remove(2))
        self.assertEqual(ring.to_list(), [1, 3, 2])
        self.assertFalse(ring.remove(99))
        self.assertEqual(len(ring), 3)

    def test_pop_front_and_back(self):
        ring = CircularDoublyLinkedList([1, 2, 3, 4])
        self.assertEqual(ring.pop_front(), 1)
        self.assertEqual(ring.pop_back(), 4)
        self.assertEqual(ring.to_list(), [2, 3])
        assert_circular(self, ring)

    def test_pop_until_empty(self):
        ring = CircularDoublyLinkedList([1, 2])
        ring.pop_back()
        ring.pop_back()
        self.assertTrue(ring.is_empty())

    def test_clear(self):
        ring = CircularDoublyLinkedList([1, 2, 3])
        ring.clear()
        self.assertEqual(len(ring), 0)
        self.assertIsNone(ring.head)
        ring.append(7)
        self.assertEqual(ring.to_list(), [7])


class EmptyListErrorTests(unittest.TestCase):
    def setUp(self):
        self.ring = CircularDoublyLinkedList()

    def test_pop_front_raises(self):
        with self.assertRaises(IndexError):
            self.ring.pop_front()

    def test_pop_back_raises(self):
        with self.assertRaises(IndexError):
            self.ring.pop_back()

    def test_remove_node_raises(self):
        with self.assertRaises(IndexError):
            self.ring.remove_node(Node(1))

    def test_node_at_raises(self):
        with self.assertRaises(IndexError):
            self.ring.node_at(0)

    def test_getitem_raises(self):
        with self.assertRaises(IndexError):
            self.ring[0]

    def test_remove_value_returns_false(self):
        self.assertFalse(self.ring.remove(1))

    def test_rotate_is_noop(self):
        self.ring.rotate(3)
        self.assertTrue(self.ring.is_empty())

    def test_find_returns_none(self):
        self.assertIsNone(self.ring.find(lambda v: True))


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.ring = CircularDoublyLinkedList(range(10))

    def test_node_at_positive(self):
        for i in range(10):
            self.assertEqual(self.ring.node_at(i).value, i)

    def test_node_at_negative(self):
        self.assertEqual(self.ring.node_at(-1).value, 9)
        self.assertEqual(self.ring.node_at(-3).value, 7)
        self.assertEqual(self.ring.node_at(-10).value, 0)

    def test_node_at_wraps(self):
        self.assertEqual(self.ring.node_at(10).value, 0)
        self.assertEqual(self.ring.node_at(13).value, 3)
        self.assertEqual(self.ring.node_at(-13).value, 7)

    def test_getitem(self):
        self.assertEqual(self.ring[4], 4)
        self.assertEqual(self.ring[-2], 8)

    def test_node_at_returns_actual_node(self):
        self.assertIs(self.ring.node_at(0), self.ring.head)
        self.assertIs(self.ring.node_at(-1), self.ring.tail)

    def test_find(self):
        node = self.ring.find(lambda v: v > 6)
        self.assertEqual(node.value, 7)
        self.assertIsNone(self.ring.find(lambda v: v > 100))

    def test_contains(self):
        self.assertIn(5, self.ring)
        self.assertNotIn(42, self.ring)

    def test_rotate_forward(self):
        self.ring.rotate(3)
        self.assertEqual(self.ring.to_list(), [3, 4, 5, 6, 7, 8, 9, 0, 1, 2])
        assert_circular(self, self.ring)

    def test_rotate_backward(self):
        self.ring.rotate(-2)
        self.assertEqual(self.ring.to_list(), [8, 9, 0, 1, 2, 3, 4, 5, 6, 7])

    def test_rotate_default_and_full_turn(self):
        self.ring.rotate()
        self.assertEqual(self.ring.head.value, 1)
        self.ring.rotate(10)
        self.assertEqual(self.ring.head.value, 1)

    def test_reversed_iteration(self):
        self.assertEqual(list(reversed(self.ring)), list(range(9, -1, -1)))

    def test_reversed_after_rotate(self):
        self.ring.rotate(5)
        self.assertEqual(list(reversed(self.ring)), [4, 3, 2, 1, 0, 9, 8, 7, 6, 5])

    def test_nodes_yields_each_node_once(self):
        nodes = list(self.ring.nodes())
        self.assertEqual(len(nodes), 10)
        self.assertEqual(len({id(n) for n in nodes}), 10)

    def test_following_links_wraps_both_ways(self):
        self.assertEqual(self.ring.tail.next.value, 0)
        self.assertEqual(self.ring.head.prev.value, 9)


class RingCursorTests(unittest.TestCase):
    def setUp(self):
        self.ring = CircularDoublyLinkedList(["a", "b", "c", "d"])
        self.cursor = RingCursor(self.ring)

    def test_starts_at_head(self):
        self.assertIs(self.cursor.ring, self.ring)
        self.assertIs(self.cursor.node, self.ring.head)
        self.assertEqual(self.cursor.value, "a")

    def test_forward(self):
        self.assertEqual(self.cursor.forward(), "b")
        self.assertEqual(self.cursor.forward(2), "d")

    def test_forward_wraps_to_head(self):
        self.cursor.forward(3)
        self.assertEqual(self.cursor.forward(), "a")

    def test_backward_wraps_to_tail(self):
        self.assertEqual(self.cursor.backward(), "d")
        self.assertEqual(self.cursor.backward(2), "b")

    def test_forward_many_turns(self):
        self.assertEqual(self.cursor.forward(4 * 5 + 2), "c")

    def test_place(self):
        self.cursor.place(self.ring.tail)
        self.assertEqual(self.cursor.value, "d")

    def test_seek_current_value(self):
        self.cursor.forward()
        self.assertTrue(self.cursor.seek(lambda v: v == "b"))
        self.assertEqual(self.cursor.value, "b")

    def test_seek_ahead_and_behind(self):
        self.assertTrue(self.cursor.seek(lambda v: v == "c"))
        self.assertEqual(self.cursor.value, "c")
        self.assertTrue(self.cursor.seek(lambda v: v == "d"))
        self.assertEqual(self.cursor.value, "d")

    def test_seek_prefers_nearest(self):
        ring = CircularDoublyLinkedList([0, 1, 2, 3, 4, 5, 6, 7])
        cursor = RingCursor(ring)
        cursor.forward(1)  # at 1
        # 0 is one step behind, 7 is two steps behind; target either even number below 1
        self.assertTrue(cursor.seek(lambda v: v in (0, 4)))
        self.assertEqual(cursor.value, 0)

    def test_seek_reaches_opposite_side(self):
        ring = CircularDoublyLinkedList(range(60))
        cursor = RingCursor(ring)
        self.assertTrue(cursor.seek(lambda v: v == 30))
        self.assertEqual(cursor.value, 30)
        self.assertTrue(cursor.seek(lambda v: v == 59))
        self.assertEqual(cursor.value, 59)

    def test_seek_missing_leaves_cursor(self):
        self.cursor.forward()
        self.assertFalse(self.cursor.seek(lambda v: v == "z"))
        self.assertEqual(self.cursor.value, "b")

    def test_detach_current_moves_to_successor(self):
        self.cursor.forward()  # b
        self.assertEqual(self.cursor.detach_current(), "b")
        self.assertEqual(self.cursor.value, "c")
        self.assertEqual(self.ring.to_list(), ["a", "c", "d"])
        assert_circular(self, self.ring)

    def test_detach_tail_wraps_to_head(self):
        self.cursor.backward()  # d
        self.assertEqual(self.cursor.detach_current(), "d")
        self.assertEqual(self.cursor.value, "a")

    def test_detach_head_updates_list_head(self):
        self.assertEqual(self.cursor.detach_current(), "a")
        self.assertEqual(self.ring.head.value, "b")
        self.assertEqual(self.cursor.value, "b")

    def test_detach_until_empty(self):
        for expected in ["a", "b", "c", "d"]:
            self.assertEqual(self.cursor.detach_current(), expected)
        self.assertTrue(self.ring.is_empty())
        self.assertIsNone(self.cursor.node)
        self.assertIsNone(self.cursor.detach_current())

    def test_cursor_over_empty_raises(self):
        cursor = RingCursor(CircularDoublyLinkedList())
        self.assertIsNone(cursor.node)
        with self.assertRaises(IndexError):
            cursor.value
        with self.assertRaises(IndexError):
            cursor.forward()
        with self.assertRaises(IndexError):
            cursor.backward()
        self.assertFalse(cursor.seek(lambda v: True))
        self.assertIsNone(cursor.detach_current())

    def test_cursor_adopts_head_once_list_is_filled(self):
        ring = CircularDoublyLinkedList()
        cursor = RingCursor(ring)
        ring.append(1)
        ring.append(2)
        self.assertEqual(cursor.value, 1)
        self.assertEqual(cursor.forward(), 2)


if __name__ == "__main__":
    unittest.main()
