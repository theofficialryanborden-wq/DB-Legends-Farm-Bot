import unittest

from dbl_farm_bot.battle import BattleAutomator
from dbl_farm_bot.config import BattleConfig, Point, Region
from dbl_farm_bot.device import DryRunDevice


class FakeDetector:
    def __init__(self, device, marker_positions):
        self.device = device
        self.marker_positions = list(marker_positions)

    def rising_rush_available(self, config):
        return True

    def template_visible(self, name):
        return "tap 900 50" in self.device.actions

    def timing_marker_x(self, config):
        if self.marker_positions:
            return self.marker_positions.pop(0)
        return None


class BattleAutomatorTest(unittest.TestCase):
    def test_times_rising_rush_when_marker_enters_perfect_zone(self):
        device = DryRunDevice()
        config = BattleConfig(
            arts_cards=[Point(1, 1)],
            rising_rush_button=Point(10, 20),
            rising_rush_pick_card=Point(30, 40),
            timing_gauge_region=Region(0, 0, 1000, 100),
            timing_perfect_x_ratio=0.9,
            timing_tolerance_px=5,
            battle_timeout=5,
            battle_poll_interval=0.1,
        )
        detector = FakeDetector(device, marker_positions=[300, 700, 898])

        result = BattleAutomator(device, detector, config, now=device.now).run()

        self.assertEqual(result.status, "victory")
        self.assertTrue(result.rising_rush_used)
        self.assertTrue(result.perfect_rising_rush_attempted)
        self.assertIn("tap 10 20", device.actions)
        self.assertIn("tap 30 40", device.actions)
        self.assertIn("tap 900 50", device.actions)


if __name__ == "__main__":
    unittest.main()
