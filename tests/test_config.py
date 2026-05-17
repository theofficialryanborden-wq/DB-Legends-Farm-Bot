import unittest

from dbl_farm_bot.config import BotConfig, DEFAULT_DEVICE_PROFILE


class ConfigTest(unittest.TestCase):
    def test_defaults_target_pixel_9a_profile(self):
        config = BotConfig()

        self.assertEqual(config.device_profile, DEFAULT_DEVICE_PROFILE)
        self.assertEqual(config.enter_event_steps[0].tap.y, 2247)
        self.assertEqual(config.battle.arts_cards[0].y, 2310)
        self.assertEqual(config.battle.rising_rush_button.y, 1988)
        self.assertEqual(config.battle.timing_gauge_region.top, 1250)


if __name__ == "__main__":
    unittest.main()
