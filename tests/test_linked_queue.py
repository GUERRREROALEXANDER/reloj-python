"""Tests for LinkedQueue."""

import unittest

from clock_app.structures import LinkedQueue


class LinkedQueueTests(unittest.TestCase):
    def setUp(self):
        self.queue = LinkedQueue()

    def test_new_queue_is_empty(self):
        self.assertTrue(self.queue.is_empty())
        self.assertEqual(len(self.queue), 0)
        self.assertEqual(list(self.queue), [])

    def test_fifo_order(self):
        for value in [1, 2, 3]:
            self.queue.enqueue(value)
        self.assertEqual(self.queue.dequeue(), 1)
        self.assertEqual(self.queue.dequeue(), 2)
        self.assertEqual(self.queue.dequeue(), 3)
        self.assertTrue(self.queue.is_empty())

    def test_peek_does_not_remove(self):
        self.queue.enqueue("a")
        self.queue.enqueue("b")
        self.assertEqual(self.queue.peek(), "a")
        self.assertEqual(len(self.queue), 2)

    def test_len_and_iteration(self):
        for value in "xyz":
            self.queue.enqueue(value)
        self.assertEqual(len(self.queue), 3)
        self.assertEqual(list(self.queue), ["x", "y", "z"])
        self.assertFalse(self.queue.is_empty())

    def test_interleaved_operations(self):
        self.queue.enqueue(1)
        self.queue.enqueue(2)
        self.assertEqual(self.queue.dequeue(), 1)
        self.queue.enqueue(3)
        self.assertEqual(self.queue.peek(), 2)
        self.assertEqual(list(self.queue), [2, 3])

    def test_reuse_after_emptying(self):
        self.queue.enqueue(1)
        self.queue.dequeue()
        self.queue.enqueue(2)
        self.assertEqual(self.queue.peek(), 2)
        self.assertEqual(len(self.queue), 1)

    def test_dequeue_empty_raises(self):
        with self.assertRaises(IndexError):
            self.queue.dequeue()

    def test_peek_empty_raises(self):
        with self.assertRaises(IndexError):
            self.queue.peek()


if __name__ == "__main__":
    unittest.main()
