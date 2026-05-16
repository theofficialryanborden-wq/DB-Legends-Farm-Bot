import unittest

from dbl_farm_bot.session import BotSession


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class BotSessionTest(unittest.TestCase):
    def test_start_sets_duration_and_active_event(self) -> None:
        clock = FakeClock()
        session = BotSession(event_names=["Raid", "Rush"], clock=clock)

        message = session.start(
            duration_minutes=15,
            rotate_events=True,
            rotation_interval_minutes=5,
            active_event_index=1,
        )

        self.assertTrue(session.is_running)
        self.assertEqual(session.active_event, "Rush")
        self.assertEqual(session.remaining_seconds(), 900)
        self.assertEqual(message, "Started farming Rush for 15 minutes.")

    def test_tick_rotates_after_interval(self) -> None:
        clock = FakeClock()
        session = BotSession(event_names=["Raid", "Rush"], clock=clock)
        session.start(duration_minutes=20, rotate_events=True, rotation_interval_minutes=5)

        clock.advance(299)
        self.assertEqual(session.tick(), [])
        self.assertEqual(session.active_event, "Raid")

        clock.advance(1)
        self.assertEqual(session.tick(), ["Rotated to Rush."])
        self.assertEqual(session.active_event, "Rush")

    def test_tick_stops_when_duration_finishes(self) -> None:
        clock = FakeClock()
        session = BotSession(event_names=["Raid"], clock=clock)
        session.start(duration_minutes=1, rotate_events=False, rotation_interval_minutes=5)

        clock.advance(60)

        self.assertEqual(session.tick(), ["Finished run duration."])
        self.assertFalse(session.is_running)
        self.assertEqual(session.remaining_seconds(), 0)

    def test_replace_events_requires_one_event(self) -> None:
        session = BotSession(event_names=["Raid"])

        with self.assertRaisesRegex(ValueError, "Keep at least one event"):
            session.replace_events([" "])


if __name__ == "__main__":
    unittest.main()
