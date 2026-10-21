"""Tests for the clock features: stopwatch, timer, alarms and world clock."""

import unittest
from datetime import datetime, timedelta

from clock_app.core import FixedOffsetTimeProvider
from clock_app.features import (
    CITY_CATALOG,
    Alarm,
    AlarmManager,
    CountdownTimer,
    Feature,
    Lap,
    Stopwatch,
    WorldClock,
    format_duration,
)
from clock_app.features.countdown_timer import DEFAULT_PRESETS
from clock_app.features.world_clock import DEFAULT_CITIES, city_from_catalog


class FakeClock:
    """Monotonic clock controlled by the test."""

    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class EventRecorder:
    def __init__(self, feature: Feature) -> None:
        self.events: list[tuple[str, object]] = []
        feature.subscribe(self)

    def __call__(self, event, payload):
        self.events.append((event, payload))

    def names(self) -> list[str]:
        return [name for name, _ in self.events]


# 2026-10-19 is a Monday.
MONDAY = datetime(2026, 10, 19)


def on(day_offset: int, hour: int, minute: int, second: int = 0) -> datetime:
    return (MONDAY + timedelta(days=day_offset)).replace(hour=hour, minute=minute, second=second)


# --------------------------------------------------------------- format_duration
class FormatDurationTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(format_duration(0), "00:00.00")
        self.assertEqual(format_duration(0, show_centis=False), "00:00")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_duration(65.5), "01:05.50")
        self.assertEqual(format_duration(59.99), "00:59.99")

    def test_hours_shown_only_when_needed(self):
        self.assertEqual(format_duration(3600), "01:00:00.00")
        self.assertEqual(format_duration(3661.25, show_centis=False), "01:01:01")
        self.assertEqual(format_duration(3599.999, show_centis=False), "59:59")

    def test_negative_clamped_to_zero(self):
        self.assertEqual(format_duration(-5), "00:00.00")

    def test_truncates_instead_of_rounding(self):
        self.assertEqual(format_duration(1.999), "00:01.99")
        self.assertEqual(format_duration(59.9999, show_centis=False), "00:59")

    def test_no_float_noise(self):
        self.assertEqual(format_duration(0.29), "00:00.29")
        self.assertEqual(format_duration(1.15), "00:01.15")
        self.assertEqual(format_duration(4.35), "00:04.35")

    def test_large_value(self):
        self.assertEqual(format_duration(100 * 3600), "100:00:00.00")


class FeatureBaseTests(unittest.TestCase):
    def test_subscribe_emit_unsubscribe(self):
        stopwatch = Stopwatch(clock=FakeClock())
        recorder = EventRecorder(stopwatch)
        stopwatch.emit("custom", 42)
        self.assertEqual(recorder.events, [("custom", 42)])
        stopwatch.unsubscribe(recorder)
        stopwatch.emit("custom", 1)
        self.assertEqual(len(recorder.events), 1)
        stopwatch.unsubscribe(recorder)  # unknown listener is ignored

    def test_feature_is_abstract(self):
        with self.assertRaises(TypeError):
            Feature("x")

    def test_features_are_polymorphic(self):
        features = [Stopwatch(clock=FakeClock()), CountdownTimer(clock=FakeClock()), AlarmManager(), WorldClock()]
        for feature in features:
            self.assertIsInstance(feature, Feature)
            feature.tick(MONDAY)
            self.assertIsInstance(feature.summary(), str)
            self.assertIn(type(feature).__name__, repr(feature))


# ------------------------------------------------------------------- Stopwatch
class StopwatchTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.sw = Stopwatch(clock=self.clock)
        self.recorder = EventRecorder(self.sw)

    def test_initial_state(self):
        self.assertFalse(self.sw.running)
        self.assertEqual(self.sw.elapsed, 0.0)
        self.assertEqual(self.sw.summary(), "Ready")
        self.assertIsNone(self.sw.lap())
        self.assertIsNone(self.sw.fastest_lap())
        self.assertIsNone(self.sw.slowest_lap())

    def test_elapsed_while_running(self):
        self.sw.start()
        self.assertTrue(self.sw.running)
        self.clock.advance(2.5)
        self.assertAlmostEqual(self.sw.elapsed, 2.5)

    def test_pause_freezes_elapsed(self):
        self.sw.start()
        self.clock.advance(3)
        self.sw.pause()
        self.clock.advance(100)
        self.assertAlmostEqual(self.sw.elapsed, 3)
        self.assertFalse(self.sw.running)

    def test_resume_accumulates(self):
        self.sw.start()
        self.clock.advance(3)
        self.sw.pause()
        self.clock.advance(10)
        self.sw.start()
        self.clock.advance(2)
        self.assertAlmostEqual(self.sw.elapsed, 5)

    def test_start_twice_does_not_restart(self):
        self.sw.start()
        self.clock.advance(4)
        self.sw.start()
        self.assertAlmostEqual(self.sw.elapsed, 4)
        self.assertEqual(self.recorder.names().count("started"), 1)

    def test_pause_when_stopped_is_noop(self):
        self.sw.pause()
        self.assertEqual(self.recorder.events, [])

    def test_toggle(self):
        self.sw.toggle()
        self.assertTrue(self.sw.running)
        self.clock.advance(1)
        self.sw.toggle()
        self.assertFalse(self.sw.running)
        self.assertEqual(self.recorder.names(), ["started", "paused"])

    def test_reset(self):
        self.sw.start()
        self.clock.advance(5)
        self.sw.lap()
        self.sw.reset()
        self.assertEqual(self.sw.elapsed, 0)
        self.assertFalse(self.sw.running)
        self.assertEqual(len(self.sw.laps), 0)
        self.assertEqual(self.recorder.names()[-1], "reset")

    def test_laps_record_split_and_total(self):
        self.sw.start()
        self.clock.advance(10)
        first = self.sw.lap()
        self.clock.advance(7)
        second = self.sw.lap()
        self.clock.advance(12)
        third = self.sw.lap()
        self.assertEqual(first, Lap(1, 10, 10))
        self.assertEqual(second, Lap(2, 7, 17))
        self.assertEqual(third, Lap(3, 12, 29))
        self.assertEqual(len(self.sw.laps), 3)
        lap_events = [payload for name, payload in self.recorder.events if name == "lap"]
        self.assertEqual(lap_events, [first, second, third])

    def test_fastest_and_slowest(self):
        self.sw.start()
        for split in [10, 7, 12, 9]:
            self.clock.advance(split)
            self.sw.lap()
        self.assertEqual(self.sw.fastest_lap().number, 2)
        self.assertEqual(self.sw.slowest_lap().number, 3)

    def test_newest_laps_first(self):
        self.sw.start()
        for _ in range(3):
            self.clock.advance(1)
            self.sw.lap()
        self.assertEqual([lap.number for lap in self.sw.newest_laps()], [3, 2, 1])

    def test_current_split(self):
        self.sw.start()
        self.clock.advance(4)
        self.assertAlmostEqual(self.sw.current_split(), 4)
        self.sw.lap()
        self.clock.advance(1.5)
        self.assertAlmostEqual(self.sw.current_split(), 1.5)

    def test_summary(self):
        self.sw.start()
        self.clock.advance(65)
        self.assertEqual(self.sw.summary(), "Running · 01:05")
        self.sw.pause()
        self.assertEqual(self.sw.summary(), "Paused · 01:05")

    def test_lap_while_paused(self):
        self.sw.start()
        self.clock.advance(3)
        self.sw.pause()
        lap = self.sw.lap()
        self.assertEqual(lap.total, 3)


# -------------------------------------------------------------- CountdownTimer
class CountdownTimerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.timer = CountdownTimer(duration=60, clock=self.clock)
        self.recorder = EventRecorder(self.timer)

    def test_initial_state(self):
        self.assertFalse(self.timer.running)
        self.assertFalse(self.timer.finished)
        self.assertEqual(self.timer.remaining, 60)
        self.assertEqual(self.timer.progress, 0)
        self.assertEqual(self.timer.summary(), "Set to 01:00")

    def test_counts_down(self):
        self.timer.start()
        self.clock.advance(15)
        self.assertAlmostEqual(self.timer.remaining, 45)
        self.assertAlmostEqual(self.timer.progress, 0.25)
        self.assertEqual(self.timer.summary(), "00:45 left")

    def test_remaining_never_negative(self):
        self.timer.start()
        self.clock.advance(500)
        self.assertEqual(self.timer.remaining, 0)
        self.assertAlmostEqual(self.timer.progress, 1.0)

    def test_pause_and_resume(self):
        self.timer.start()
        self.clock.advance(20)
        self.timer.pause()
        self.clock.advance(1000)
        self.assertAlmostEqual(self.timer.remaining, 40)
        self.assertEqual(self.timer.summary(), "Paused · 00:40")
        self.timer.start()
        self.clock.advance(10)
        self.assertAlmostEqual(self.timer.remaining, 30)

    def test_start_twice_is_noop(self):
        self.timer.start()
        self.clock.advance(5)
        self.timer.start()
        self.assertAlmostEqual(self.timer.remaining, 55)
        self.assertEqual(self.recorder.names().count("started"), 1)

    def test_toggle(self):
        self.timer.toggle()
        self.assertTrue(self.timer.running)
        self.timer.toggle()
        self.assertFalse(self.timer.running)

    def test_finished_event_emitted_once(self):
        self.timer.start()
        self.clock.advance(59.9)
        self.timer.tick(MONDAY)
        self.assertNotIn("finished", self.recorder.names())
        self.clock.advance(0.2)
        self.timer.tick(MONDAY)
        self.timer.tick(MONDAY)
        self.assertEqual(self.recorder.names().count("finished"), 1)
        self.assertTrue(self.timer.finished)
        self.assertFalse(self.timer.running)
        self.assertEqual(self.timer.remaining, 0)
        self.assertEqual(self.timer.summary(), "Time's up!")

    def test_tick_when_not_running_does_nothing(self):
        self.timer.tick(MONDAY)
        self.assertFalse(self.timer.finished)
        self.assertEqual(self.recorder.events, [])

    def test_restart_after_finish_uses_full_duration(self):
        self.timer.start()
        self.clock.advance(60)
        self.timer.tick(MONDAY)
        self.timer.start()
        self.assertFalse(self.timer.finished)
        self.assertAlmostEqual(self.timer.remaining, 60)

    def test_reset(self):
        self.timer.start()
        self.clock.advance(30)
        self.timer.reset()
        self.assertFalse(self.timer.running)
        self.assertEqual(self.timer.remaining, 60)
        self.assertEqual(self.recorder.names()[-1], "reset")

    def test_set_duration(self):
        self.timer.set_duration(90)
        self.assertEqual(self.timer.duration, 90)
        self.assertEqual(self.timer.remaining, 90)
        self.assertIn(("changed", 90.0), self.recorder.events)

    def test_set_duration_minimum_is_one_second(self):
        self.timer.set_duration(0)
        self.assertEqual(self.timer.duration, 1.0)

    def test_add_time_while_running(self):
        self.timer.start()
        self.clock.advance(50)
        self.timer.add_time(60)
        self.assertAlmostEqual(self.timer.remaining, 70)
        self.assertEqual(self.timer.duration, 120)

    def test_add_time_while_paused(self):
        self.timer.add_time(30)
        self.assertEqual(self.timer.remaining, 90)
        self.assertEqual(self.timer.duration, 90)

    def test_add_time_after_finish_clears_flag(self):
        self.timer.start()
        self.clock.advance(60)
        self.timer.tick(MONDAY)
        self.timer.add_time(30)
        self.assertFalse(self.timer.finished)
        self.timer.start()
        self.assertAlmostEqual(self.timer.remaining, 30)

    def test_cursor_starts_on_matching_preset(self):
        timer = CountdownTimer(duration=600, clock=self.clock)
        self.assertEqual(timer.preset_cursor.value, 600)

    def test_next_and_previous_preset(self):
        timer = CountdownTimer(duration=300, clock=self.clock)
        self.assertEqual(timer.next_preset(), 600)
        self.assertEqual(timer.duration, 600)
        self.assertEqual(timer.previous_preset(), 300)
        self.assertEqual(timer.previous_preset(), 180)

    def test_presets_wrap_forward(self):
        timer = CountdownTimer(duration=DEFAULT_PRESETS[-1], clock=self.clock)
        self.assertEqual(timer.next_preset(), DEFAULT_PRESETS[0])

    def test_presets_wrap_backward(self):
        self.assertEqual(self.timer.previous_preset(), DEFAULT_PRESETS[-1])
        self.assertEqual(self.timer.duration, DEFAULT_PRESETS[-1])

    def test_full_cycle_of_presets(self):
        seen = [self.timer.next_preset() for _ in range(len(DEFAULT_PRESETS))]
        self.assertEqual(seen, list(DEFAULT_PRESETS[1:]) + [DEFAULT_PRESETS[0]])

    def test_preset_change_stops_running_timer(self):
        self.timer.start()
        self.timer.next_preset()
        self.assertFalse(self.timer.running)


# ----------------------------------------------------------------------- Alarm
class AlarmTests(unittest.TestCase):
    def test_monday_constant_is_monday(self):
        self.assertEqual(MONDAY.weekday(), 0)

    def test_invalid_time(self):
        for hour, minute in [(24, 0), (-1, 0), (0, 60), (0, -1)]:
            with self.assertRaises(ValueError):
                Alarm(hour, minute)

    def test_unique_ids(self):
        self.assertNotEqual(Alarm(1, 0).id, Alarm(1, 0).id)

    def test_time_text(self):
        self.assertEqual(Alarm(7, 5).time_text(), "07:05")
        self.assertEqual(Alarm(0, 0).time_text(use_24h=False), "12:00 AM")
        self.assertEqual(Alarm(12, 30).time_text(use_24h=False), "12:30 PM")
        self.assertEqual(Alarm(18, 45).time_text(use_24h=False), "6:45 PM")

    def test_days_text(self):
        self.assertEqual(Alarm(1, 0).days_text(), "Every day")
        self.assertEqual(Alarm(1, 0, days=frozenset(range(7))).days_text(), "Every day")
        self.assertEqual(Alarm(1, 0, days=frozenset(range(5))).days_text(), "Weekdays")
        self.assertEqual(Alarm(1, 0, days=frozenset({5, 6})).days_text(), "Weekends")
        self.assertEqual(Alarm(1, 0, days=frozenset({4, 0, 2})).days_text(), "Mon Wed Fri")

    def test_rings_on(self):
        alarm = Alarm(1, 0, days=frozenset({0, 3}))
        self.assertTrue(alarm.rings_on(0))
        self.assertFalse(alarm.rings_on(1))
        self.assertTrue(Alarm(1, 0).rings_on(6))

    def test_next_occurrence_later_today(self):
        alarm = Alarm(8, 0)
        self.assertEqual(alarm.next_occurrence(on(0, 7, 0)), on(0, 8, 0))

    def test_next_occurrence_tomorrow_when_passed(self):
        alarm = Alarm(8, 0)
        self.assertEqual(alarm.next_occurrence(on(0, 9, 0)), on(1, 8, 0))
        self.assertEqual(alarm.next_occurrence(on(0, 8, 0)), on(1, 8, 0))

    def test_next_occurrence_skips_to_allowed_day(self):
        alarm = Alarm(8, 0, days=frozenset({4}))  # Fridays only
        self.assertEqual(alarm.next_occurrence(on(0, 7, 0)), on(4, 8, 0))
        self.assertEqual(alarm.next_occurrence(on(4, 9, 0)), on(11, 8, 0))


# --------------------------------------------------------------- AlarmManager
class AlarmManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = AlarmManager()
        self.recorder = EventRecorder(self.manager)

    def test_empty(self):
        self.assertEqual(len(self.manager), 0)
        self.assertEqual(self.manager.summary(), "No alarms")
        self.assertIsNone(self.manager.next_alarm(on(0, 12, 0)))

    def test_alarms_kept_sorted(self):
        for hour, minute in [(9, 30), (6, 0), (22, 15), (6, 45), (0, 5)]:
            self.manager.add(hour, minute)
        times = [(a.hour, a.minute) for a in self.manager]
        self.assertEqual(times, [(0, 5), (6, 0), (6, 45), (9, 30), (22, 15)])
        self.assertEqual(len(self.manager), 5)
        self.assertEqual(self.recorder.names(), ["changed"] * 5)

    def test_add_blank_label_defaults(self):
        self.assertEqual(self.manager.add(7, 0, "   ").label, "Alarm")
        self.assertEqual(self.manager.add(7, 0, "  Gym ").label, "Gym")

    def test_add_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.manager.add(25, 0)
        self.assertEqual(len(self.manager), 0)

    def test_remove(self):
        a = self.manager.add(7, 0)
        b = self.manager.add(8, 0)
        self.assertTrue(self.manager.remove(a.id))
        self.assertEqual(list(self.manager), [b])
        self.assertFalse(self.manager.remove(a.id))

    def test_toggle(self):
        alarm = self.manager.add(7, 0)
        alarm.snoozed_until = on(0, 7, 5)
        self.assertIs(self.manager.toggle(alarm.id), alarm)
        self.assertFalse(alarm.enabled)
        self.assertIsNone(alarm.snoozed_until)
        self.manager.toggle(alarm.id)
        self.assertTrue(alarm.enabled)
        self.assertIsNone(self.manager.toggle(-1))

    def test_summary(self):
        a = self.manager.add(7, 0)
        self.manager.add(8, 0)
        self.manager.toggle(a.id)
        self.assertEqual(self.manager.summary(), "1 of 2 active")

    def test_tick_fires_at_matching_minute(self):
        alarm = self.manager.add(7, 30, "Wake")
        self.manager.tick(on(0, 7, 29, 59))
        self.assertTrue(self.manager.pending.is_empty())
        self.manager.tick(on(0, 7, 30, 0))
        self.assertEqual(len(self.manager.pending), 1)
        self.assertIs(self.manager.pending.peek(), alarm)
        self.assertIn(("ringing", alarm), self.recorder.events)

    def test_tick_fires_only_once_per_minute(self):
        self.manager.add(7, 30)
        for second in range(0, 60, 5):
            self.manager.tick(on(0, 7, 30, second))
        self.assertEqual(len(self.manager.pending), 1)
        self.assertEqual(self.recorder.names().count("ringing"), 1)

    def test_tick_fires_again_next_day(self):
        self.manager.add(7, 30)
        self.manager.tick(on(0, 7, 30))
        self.manager.tick(on(1, 7, 30))
        self.assertEqual(len(self.manager.pending), 2)

    def test_disabled_alarm_does_not_fire(self):
        alarm = self.manager.add(7, 30)
        self.manager.toggle(alarm.id)
        self.manager.tick(on(0, 7, 30))
        self.assertTrue(self.manager.pending.is_empty())

    def test_weekday_filtering(self):
        self.manager.add(7, 0, days=frozenset({5, 6}))  # weekends
        self.manager.tick(on(0, 7, 0))  # Monday
        self.assertTrue(self.manager.pending.is_empty())
        self.manager.tick(on(5, 7, 0))  # Saturday
        self.assertEqual(len(self.manager.pending), 1)

    def test_multiple_alarms_same_minute_queue_in_order(self):
        first = self.manager.add(7, 0, "first")
        second = self.manager.add(7, 0, "second")
        self.manager.tick(on(0, 7, 0))
        self.assertEqual(self.manager.pending.dequeue(), first)
        self.assertEqual(self.manager.pending.dequeue(), second)

    def test_snooze_fires_after_five_minutes(self):
        alarm = self.manager.add(7, 0)
        self.manager.tick(on(0, 7, 0, 0))
        self.manager.pending.dequeue()
        self.manager.snooze(alarm, on(0, 7, 0, 20))
        self.assertEqual(alarm.snoozed_until, on(0, 7, 5))
        self.manager.tick(on(0, 7, 4, 59))
        self.assertTrue(self.manager.pending.is_empty())
        self.manager.tick(on(0, 7, 5, 0))
        self.assertIs(self.manager.pending.dequeue(), alarm)
        self.assertIsNone(alarm.snoozed_until)
        self.manager.tick(on(0, 7, 5, 30))
        self.assertTrue(self.manager.pending.is_empty())

    def test_snooze_blocks_regular_firing(self):
        alarm = self.manager.add(7, 0)
        self.manager.snooze(alarm, on(0, 6, 58))  # snoozed until 7:03
        self.manager.tick(on(0, 7, 0))
        self.assertTrue(self.manager.pending.is_empty())
        self.manager.tick(on(0, 7, 3))
        self.assertEqual(len(self.manager.pending), 1)

    def test_dismiss_clears_snooze(self):
        alarm = self.manager.add(7, 0)
        self.manager.snooze(alarm, on(0, 7, 0))
        self.manager.dismiss(alarm)
        self.assertIsNone(alarm.snoozed_until)
        self.manager.tick(on(0, 7, 5))
        self.assertTrue(self.manager.pending.is_empty())

    def test_next_alarm_later_today(self):
        self.manager.add(6, 0)
        later = self.manager.add(14, 0)
        self.manager.add(20, 0)
        alarm, when = self.manager.next_alarm(on(0, 12, 0))
        self.assertIs(alarm, later)
        self.assertEqual(when, on(0, 14, 0))

    def test_next_alarm_wraps_past_midnight(self):
        early = self.manager.add(6, 0)
        self.manager.add(14, 0)
        alarm, when = self.manager.next_alarm(on(0, 23, 0))
        self.assertIs(alarm, early)
        self.assertEqual(when, on(1, 6, 0))

    def test_next_alarm_ignores_disabled(self):
        a = self.manager.add(13, 0)
        b = self.manager.add(15, 0)
        self.manager.toggle(a.id)
        self.assertIs(self.manager.next_alarm(on(0, 12, 0))[0], b)
        self.manager.toggle(b.id)
        self.assertIsNone(self.manager.next_alarm(on(0, 12, 0)))

    def test_next_alarm_respects_weekdays(self):
        weekend = self.manager.add(8, 0, days=frozenset({5}))
        daily = self.manager.add(9, 0)
        self.assertIs(self.manager.next_alarm(on(0, 12, 0))[0], daily)
        self.assertEqual(weekend.next_occurrence(on(0, 12, 0)), on(5, 8, 0))

    def test_next_alarm_uses_snooze_time(self):
        alarm = self.manager.add(7, 0)
        self.manager.add(10, 0)
        self.manager.snooze(alarm, on(0, 7, 0))
        found, when = self.manager.next_alarm(on(0, 7, 1))
        self.assertIs(found, alarm)
        self.assertEqual(when, on(0, 7, 5))

    def test_remove_forgets_fired_stamp(self):
        alarm = self.manager.add(7, 0)
        self.manager.tick(on(0, 7, 0))
        self.manager.remove(alarm.id)
        self.assertNotIn(alarm.id, self.manager._last_fired)


# ------------------------------------------------------------------ WorldClock
def offsets(clock: WorldClock) -> list[float]:
    return [city.utc_offset().total_seconds() / 3600 for city in clock]


class WorldClockTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldClock()
        self.recorder = EventRecorder(self.world)

    def names(self) -> list[str]:
        return [city.name for city in self.world]

    def test_default_cities_sorted_by_offset(self):
        self.assertEqual(set(self.names()), set(DEFAULT_CITIES))
        self.assertEqual(offsets(self.world), sorted(offsets(self.world)))
        self.assertEqual(self.world.selected.name, "New York")

    def test_next_city_wraps(self):
        visited = [self.world.next_city().name for _ in range(len(DEFAULT_CITIES))]
        self.assertEqual(visited, self.names()[1:] + [self.names()[0]])
        self.assertEqual(self.recorder.names(), ["selected"] * len(DEFAULT_CITIES))

    def test_previous_city_wraps(self):
        self.assertEqual(self.world.previous_city().name, self.names()[-1])
        self.assertEqual(self.world.previous_city().name, self.names()[-2])

    def test_select(self):
        self.world.select("Tokyo")
        self.assertEqual(self.world.selected.name, "Tokyo")
        self.assertEqual(self.recorder.events[-1], ("selected", self.world.selected))

    def test_select_unknown_does_nothing(self):
        self.world.select("Atlantis")
        self.assertEqual(self.world.selected.name, "New York")
        self.assertEqual(self.recorder.events, [])

    def test_add_city_keeps_offset_order(self):
        for name in ["Paris", "Honolulu", "New Delhi", "Auckland", "Bogotá"]:
            self.assertTrue(self.world.add_city(name))
            self.assertEqual(self.world.selected.name, name)
            self.assertEqual(offsets(self.world), sorted(offsets(self.world)))
        self.assertEqual(self.names()[0], "Honolulu")
        self.assertEqual(self.names()[-1], "Auckland")
        self.assertIn("changed", self.recorder.names())

    def test_add_city_on_unsorted_custom_start(self):
        world = WorldClock(("Tokyo", "Lima", "London"))
        self.assertEqual([c.name for c in world], ["Lima", "London", "Tokyo"])
        world.add_city("Dubai")
        self.assertEqual([c.name for c in world], ["Lima", "London", "Dubai", "Tokyo"])

    def test_duplicates_rejected(self):
        before = self.names()
        self.assertFalse(self.world.add_city("Tokyo"))
        self.assertEqual(self.names(), before)

    def test_unknown_city_raises(self):
        with self.assertRaises(KeyError):
            self.world.add_city("Atlantis")
        with self.assertRaises(KeyError):
            city_from_catalog("Atlantis")

    def test_remove_selected(self):
        self.world.select("London")
        expected_next = self.names()[self.names().index("London") + 1]
        removed = self.world.remove_selected()
        self.assertEqual(removed.name, "London")
        self.assertNotIn("London", self.names())
        self.assertEqual(self.world.selected.name, expected_next)

    def test_remove_selected_last_wraps_to_first(self):
        self.world.previous_city()
        self.world.remove_selected()
        self.assertEqual(self.world.selected.name, self.names()[0])

    def test_remove_all_then_empty(self):
        for _ in range(len(DEFAULT_CITIES)):
            self.assertIsNotNone(self.world.remove_selected())
        self.assertIsNone(self.world.selected)
        self.assertIsNone(self.world.remove_selected())
        self.assertIsNone(self.world.next_city())
        self.assertIsNone(self.world.previous_city())
        self.assertEqual(self.world.summary(), "No cities")

    def test_add_after_emptying(self):
        for _ in range(len(DEFAULT_CITIES)):
            self.world.remove_selected()
        self.world.add_city("Lima")
        self.assertEqual(self.world.selected.name, "Lima")

    def test_available_cities(self):
        available = self.world.available_cities()
        self.assertEqual(len(available), len(CITY_CATALOG) - len(DEFAULT_CITIES))
        self.assertNotIn("Tokyo", available)
        self.assertIn("Lima", available)
        self.world.add_city("Lima")
        self.assertNotIn("Lima", self.world.available_cities())

    def test_difference_from_local(self):
        self.world.local = FixedOffsetTimeProvider("Here", -5)
        self.assertEqual(self.world.difference_from_local(city_from_catalog("Lima")), "Same time")
        self.assertEqual(self.world.difference_from_local(city_from_catalog("Tokyo")), "+14 h")
        self.assertEqual(self.world.difference_from_local(city_from_catalog("New Delhi")), "+10.5 h")
        self.assertEqual(self.world.difference_from_local(city_from_catalog("Honolulu")), "−5 h")

    def test_summary_shows_selected_city(self):
        self.assertTrue(self.world.summary().startswith("New York "))

    def test_catalog_entries_are_valid(self):
        names = [name for name, _, _ in CITY_CATALOG]
        self.assertEqual(len(names), len(set(names)))
        for name in DEFAULT_CITIES:
            self.assertIn(name, names)


if __name__ == "__main__":
    unittest.main()
