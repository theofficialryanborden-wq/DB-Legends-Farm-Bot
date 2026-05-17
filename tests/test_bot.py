import unittest

from dbl_farm_bot.bot import DragonBallLegendsBot
from dbl_farm_bot.cli import NoopBattleDetector
from dbl_farm_bot.config import BotConfig
from dbl_farm_bot.device import DryRunDevice


class BotTest(unittest.TestCase):
    def test_dry_run_farm_cycle_navigates_battle_and_post_steps(self):
        device = DryRunDevice()
        config = BotConfig()
        config = type(config).from_dict(
            {
                "cycles": 1,
                "battle": {"battle_timeout": 0.5},
            }
        )

        result = DragonBallLegendsBot(
            device,
            config,
            detector=NoopBattleDetector(),
            now=device.now,
        ).farm_events()

        self.assertEqual(len(result.cycles), 1)
        self.assertEqual(result.cycles[0].battle.status, "timeout")
        self.assertIn("tap 920 2247", device.actions)
        self.assertIn("tap 360 2310", device.actions)
        self.assertIn("tap 900 2323", device.actions)


if __name__ == "__main__":
    unittest.main()
