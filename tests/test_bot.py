import unittest
from io import BytesIO
import tempfile
from pathlib import Path

from PIL import Image

from dbl_farm_bot.bot import DragonBallLegendsBot, MenuNavigator, NavigationError
from dbl_farm_bot.cli import NoopBattleDetector
from dbl_farm_bot.config import BotConfig, NavigationStep, Point, Region, TemplateConfig
from dbl_farm_bot.device import DryRunDevice
from dbl_farm_bot.vision import ScreenAnalyzer


class BotTest(unittest.TestCase):
    def test_dry_run_farm_cycle_navigates_battle_and_post_steps(self):
        device = DryRunDevice()
        config = BotConfig()
        config = type(config).from_dict(
            {
                "allow_blind_menu_taps": True,
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

    def test_real_farm_cycle_refuses_unrecognized_menu(self):
        device = DryRunDevice()

        with self.assertRaisesRegex(NavigationError, "Template 'events_button' is not configured"):
            DragonBallLegendsBot(
                device,
                BotConfig.from_dict({"battle": {"battle_timeout": 0.5}}),
                detector=NoopBattleDetector(),
                now=device.now,
            ).farm_events()

    def test_template_navigation_taps_matched_button_center(self):
        with tempfile.TemporaryDirectory() as directory:
            template_path = Path(directory) / "events_button.png"
            Image.new("RGB", (10, 10), (255, 0, 0)).save(template_path)

            screenshot = Image.new("RGB", (80, 80), (0, 0, 0))
            for x in range(20, 30):
                for y in range(30, 40):
                    screenshot.putpixel((x, y), (255, 0, 0))
            payload = BytesIO()
            screenshot.save(payload, format="PNG")

            device = DryRunDevice(screenshot_bytes=payload.getvalue())
            analyzer = ScreenAnalyzer(
                [
                    TemplateConfig(
                        name="events_button",
                        path=str(template_path),
                        threshold=0.99,
                        region=Region(15, 25, 45, 55),
                        stride=1,
                    )
                ]
            )

            MenuNavigator(device, analyzer, now=device.now).run(
                [NavigationStep(name="events", tap_template="events_button")]
            )

        self.assertIn("tap 25 35", device.actions)


if __name__ == "__main__":
    unittest.main()
