"""Tests for the dial, the hands, the time providers and the clock engine."""

import math
import unittest
from datetime import datetime, timedelta, timezone

from clock_app.core import (
    ClockEngine,
    DialMark,
    DialRing,
    FixedOffsetTimeProvider,
    Hand,
    HourHand,
    MinuteHand,
    SecondHand,
    SystemTimeProvider,
    TimeProvider,
)


class FakeTimeProvider(TimeProvider):
    """Deterministic provider: returns whatever moment the test sets."""

    def __init__(self, moment: datetime, name: str = "Fake") -> None:
        super().__init__(name)
        self.moment = moment
        self.calls = 0

    def now(self) -> datetime:
        self.calls += 1
        return self.moment

    def utc_offset(self) -> timedelta:
        return self.moment.utcoffset() or timedelta(0)


def at(hour: int, minute: int = 0, second: int = 0, microsecond: int = 0) -> datetime:
    return datetime(2026, 10, 20, hour, minute, second, microsecond, tzinfo=timezone.utc)


class DialTests(unittest.TestCase):
    def test_ring_has_all_marks_in_order(self):
        ring = DialRing(60)
        self.assertEqual(len(ring), 60)
        self.assertEqual([m.index for m in ring], list(range(60)))

    def test_ring_wraps_from_last_to_first(self):
        ring = DialRing(60)
        self.assertEqual(ring.marks.tail.next.value.index, 0)
        self.assertEqual(ring.marks.head.prev.value.index, 59)

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            DialRing(0)
        with self.assertRaises(ValueError):
            DialRing(-5)

    def test_mark_angle_and_major(self):
        self.assertEqual(DialMark(15, 60).angle, 90.0)
        self.assertTrue(DialMark(15, 60).is_major)
        self.assertFalse(DialMark(16, 60).is_major)
        self.assertTrue(DialMark(7, 12).is_major)
        self.assertTrue(DialMark(1, 4).is_major)

    def test_cursor_starts_at_zero(self):
        self.assertEqual(DialRing(12).cursor().value.index, 0)


class HandAngleTests(unittest.TestCase):
    def test_three_oclock(self):
        hour, minute, second = HourHand(), MinuteHand(), SecondHand()
        for hand in (hour, minute, second):
            hand.update(at(3))
        self.assertAlmostEqual(hour.angle, 90.0)
        self.assertAlmostEqual(minute.angle, 0.0)
        self.assertAlmostEqual(second.angle, 0.0)
        self.assertEqual(hour.position, 3)

    def test_six_thirty(self):
        hour, minute = HourHand(), MinuteHand()
        hour.update(at(6, 30))
        minute.update(at(6, 30))
        self.assertAlmostEqual(hour.angle, 195.0)
        self.assertAlmostEqual(minute.angle, 180.0)

    def test_afternoon_uses_twelve_hour_dial(self):
        hand = HourHand()
        hand.update(at(15))
        self.assertEqual(hand.position, 3)
        self.assertAlmostEqual(hand.angle, 90.0)
        hand.update(at(0))
        self.assertAlmostEqual(hand.angle, 0.0)

    def test_hour_hand_includes_seconds(self):
        hand = HourHand()
        hand.update(at(9, 59, 60 - 1))
        expected = (9 + (59 + 59 / 60) / 60) * 30
        self.assertAlmostEqual(hand.angle, expected)

    def test_minute_hand_includes_seconds(self):
        hand = MinuteHand()
        hand.update(at(1, 45, 30))
        self.assertAlmostEqual(hand.angle, 45.5 * 6)

    def test_minute_hand_includes_microseconds(self):
        hand = MinuteHand()
        hand.update(at(1, 10, 0, 500_000))
        self.assertAlmostEqual(hand.angle, (10 + 0.5 / 60) * 6)

    def test_smooth_second_hand(self):
        hand = SecondHand(smooth=True)
        hand.update(at(1, 0, 15, 500_000))
        self.assertAlmostEqual(hand.angle, 15.5 * 6)

    def test_ticking_second_hand(self):
        hand = SecondHand(smooth=False)
        hand.update(at(1, 0, 15, 500_000))
        self.assertAlmostEqual(hand.angle, 90.0)

    def test_names(self):
        self.assertEqual(HourHand().name, "hour")
        self.assertEqual(MinuteHand().name, "minute")
        self.assertEqual(SecondHand().name, "second")

    def test_read_returns_position_and_fraction(self):
        self.assertEqual(HourHand().read(at(18, 15)), (6, 0.25))
        self.assertEqual(MinuteHand().read(at(0, 20, 30)), (20, 0.5))
        self.assertEqual(SecondHand(smooth=False).read(at(0, 0, 42, 999_999)), (42, 0.0))

    def test_hand_is_abstract(self):
        with self.assertRaises(TypeError):
            Hand(60)

    def test_repr(self):
        hand = HourHand()
        hand.update(at(3))
        self.assertEqual(repr(hand), "HourHand(position=3, angle=90.0)")


class HandCursorTests(unittest.TestCase):
    def test_normal_tick_moves_one_node(self):
        hand = SecondHand(smooth=False)
        for second in range(60):
            hand.update(at(0, 0, second))
            self.assertEqual(hand.position, second)

    def test_wraps_from_59_to_0(self):
        hand = SecondHand(smooth=False)
        hand.update(at(0, 0, 59))
        self.assertEqual(hand.position, 59)
        hand.update(at(0, 1, 0))
        self.assertEqual(hand.position, 0)
        self.assertAlmostEqual(hand.angle, 0.0)

    def test_jump_forward_and_backward(self):
        hand = MinuteHand()
        hand.update(at(0, 40))
        self.assertEqual(hand.position, 40)
        hand.update(at(0, 5))
        self.assertEqual(hand.position, 5)
        hand.update(at(0, 35))
        self.assertEqual(hand.position, 35)

    def test_jump_to_opposite_side(self):
        hand = MinuteHand()
        hand.update(at(0, 30))
        self.assertEqual(hand.position, 30)
        self.assertAlmostEqual(hand.angle, 180.0)

    def test_hour_hand_jumps_across_dial(self):
        hand = HourHand()
        hand.update(at(11))
        self.assertEqual(hand.position, 11)
        hand.update(at(5))
        self.assertEqual(hand.position, 5)

    def test_same_position_keeps_cursor(self):
        hand = MinuteHand()
        hand.update(at(0, 12, 0))
        node = hand._cursor.node
        hand.update(at(0, 12, 30))
        self.assertIs(hand._cursor.node, node)
        self.assertAlmostEqual(hand.angle, 12.5 * 6)


class PolygonTests(unittest.TestCase):
    def test_blade_tip_at_twelve(self):
        hand = MinuteHand()
        hand.update(at(0, 0))
        points = hand.polygon(100, 100, 50)
        self.assertEqual(len(points), 10)
        tip_x, tip_y = points[4], points[5]
        self.assertAlmostEqual(tip_x, 100)
        self.assertAlmostEqual(tip_y, 100 - 50 * MinuteHand.style.length)

    def test_blade_tip_at_three(self):
        hand = HourHand()
        hand.update(at(3))
        points = hand.polygon(0, 0, 100)
        self.assertAlmostEqual(points[4], 100 * HourHand.style.length)
        self.assertAlmostEqual(points[5], 0, places=6)

    def test_second_hand_is_a_line(self):
        hand = SecondHand(smooth=False)
        hand.update(at(0, 0, 15))
        x0, y0, x1, y1 = hand.polygon(0, 0, 100)
        self.assertAlmostEqual(x0, -100 * SecondHand.style.tail)
        self.assertAlmostEqual(y0, 0, places=6)
        self.assertAlmostEqual(x1, 100 * SecondHand.style.length)
        self.assertAlmostEqual(y1, 0, places=6)

    def test_counterweight_opposite_to_tip(self):
        hand = SecondHand(smooth=False)
        hand.update(at(0, 0, 0))
        x, y = hand.counterweight(0, 0, 100)
        self.assertAlmostEqual(x, 0, places=6)
        self.assertAlmostEqual(y, 100 * SecondHand.style.tail * 0.75)


class TimeProviderTests(unittest.TestCase):
    def test_fixed_offset_now_has_offset(self):
        provider = FixedOffsetTimeProvider("Tokyo", 9, "Japan")
        now = provider.now()
        self.assertEqual(now.utcoffset(), timedelta(hours=9))
        self.assertEqual(provider.country, "Japan")
        delta = abs(now - datetime.now(timezone.utc))
        self.assertLess(delta, timedelta(seconds=5))

    def test_offset_labels(self):
        self.assertEqual(FixedOffsetTimeProvider("A", 9).offset_label(), "UTC+09:00")
        self.assertEqual(FixedOffsetTimeProvider("B", -5).offset_label(), "UTC-05:00")
        self.assertEqual(FixedOffsetTimeProvider("C", 5.5).offset_label(), "UTC+05:30")
        self.assertEqual(FixedOffsetTimeProvider("D", 0).offset_label(), "UTC+00:00")
        self.assertEqual(FixedOffsetTimeProvider("E", -3.5).offset_label(), "UTC-03:30")

    def test_fixed_offset_equality_by_name(self):
        self.assertEqual(FixedOffsetTimeProvider("X", 1), FixedOffsetTimeProvider("X", 2))
        self.assertNotEqual(FixedOffsetTimeProvider("X", 1), FixedOffsetTimeProvider("Y", 1))
        self.assertEqual(len({FixedOffsetTimeProvider("X", 1), FixedOffsetTimeProvider("X", 1)}), 1)

    def test_system_provider_is_aware(self):
        provider = SystemTimeProvider()
        self.assertEqual(provider.name, "Local")
        self.assertIsNotNone(provider.now().tzinfo)
        self.assertIsInstance(provider.utc_offset(), timedelta)

    def test_repr(self):
        self.assertEqual(repr(FixedOffsetTimeProvider("Lima", -5)), "FixedOffsetTimeProvider('Lima')")

    def test_time_provider_is_abstract(self):
        with self.assertRaises(TypeError):
            TimeProvider("x")


class ClockEngineTests(unittest.TestCase):
    def test_engine_reads_from_injected_provider(self):
        provider = FakeTimeProvider(at(3))
        engine = ClockEngine(provider)
        self.assertIs(engine.provider, provider)
        self.assertEqual(engine.moment, at(3))
        self.assertAlmostEqual(engine.hour_hand.angle, 90.0)
        self.assertAlmostEqual(engine.minute_hand.angle, 0.0)
        self.assertAlmostEqual(engine.second_hand.angle, 0.0)

    def test_hands_order(self):
        engine = ClockEngine(FakeTimeProvider(at(1)))
        self.assertEqual([h.name for h in engine.hands], ["hour", "minute", "second"])
        for hand in engine.hands:
            self.assertIsInstance(hand, Hand)

    def test_polymorphic_hands_share_interface(self):
        engine = ClockEngine(FakeTimeProvider(at(6, 30, 15)), smooth_seconds=False)
        angles = {hand.name: hand.angle for hand in engine.hands}
        self.assertAlmostEqual(angles["hour"], (6 + (30 + 15 / 60) / 60) * 30)
        self.assertAlmostEqual(angles["minute"], (30 + 15 / 60) * 6)
        self.assertAlmostEqual(angles["second"], 90.0)

    def test_tick_follows_provider(self):
        provider = FakeTimeProvider(at(6, 30))
        engine = ClockEngine(provider)
        provider.moment = at(9, 15, 45)
        self.assertEqual(engine.tick(), at(9, 15, 45))
        self.assertAlmostEqual(engine.hour_hand.angle, (9 + (15 + 45 / 60) / 60) * 30)
        self.assertEqual(engine.minute_hand.position, 15)
        self.assertEqual(engine.second_hand.position, 45)

    def test_use_provider_switches_and_ticks(self):
        engine = ClockEngine(FakeTimeProvider(at(3)))
        other = FakeTimeProvider(at(10, 20), name="Other")
        engine.use_provider(other)
        self.assertIs(engine.provider, other)
        self.assertEqual(engine.hour_hand.position, 10)
        self.assertEqual(engine.minute_hand.position, 20)

    def test_smooth_seconds_toggle(self):
        provider = FakeTimeProvider(at(0, 0, 10, 250_000))
        engine = ClockEngine(provider, smooth_seconds=True)
        self.assertTrue(engine.smooth_seconds)
        self.assertAlmostEqual(engine.second_hand.angle, 10.25 * 6)
        engine.smooth_seconds = False
        self.assertFalse(engine.second_hand.smooth)
        engine.tick()
        self.assertAlmostEqual(engine.second_hand.angle, 60.0)

    def test_default_provider_is_system(self):
        engine = ClockEngine()
        self.assertIsInstance(engine.provider, SystemTimeProvider)

    def test_fixed_offset_provider_in_engine(self):
        engine = ClockEngine(FixedOffsetTimeProvider("Tokyo", 9))
        self.assertEqual(engine.moment.utcoffset(), timedelta(hours=9))
        self.assertEqual(engine.hour_hand.position, engine.moment.hour % 12)

    def test_many_ticks_keep_cursor_in_sync(self):
        provider = FakeTimeProvider(at(11, 58, 0))
        engine = ClockEngine(provider, smooth_seconds=False)
        moment = at(11, 58, 0)
        for _ in range(5 * 60):
            moment += timedelta(seconds=1)
            provider.moment = moment
            engine.tick()
            self.assertEqual(engine.second_hand.position, moment.second)
            self.assertEqual(engine.minute_hand.position, moment.minute)
            self.assertEqual(engine.hour_hand.position, moment.hour % 12)
        self.assertTrue(math.isclose(engine.hour_hand.angle, (0 + 3 / 60) * 30))


if __name__ == "__main__":
    unittest.main()
