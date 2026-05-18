import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class GuiTest(unittest.TestCase):
    def test_gui_module_imports_without_opening_window(self):
        from dbl_farm_bot import gui

        self.assertTrue(callable(gui.main))

    def test_add_template_saves_template_to_config(self):
        from dbl_farm_bot.config import BotConfig
        from dbl_farm_bot.gui import FarmBotApp

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            BotConfig().save(config_path)
            app = _template_app(config_path)

            app.add_template()

            config = BotConfig.load(config_path)
            self.assertEqual(len(config.templates), 1)
            template = config.templates[0]
            self.assertEqual(template.name, "victory")
            self.assertEqual(template.path, "templates/victory.png")
            self.assertEqual(template.threshold, 0.91)
            self.assertEqual(template.stride, 2)
            self.assertIsNotNone(template.region)
            self.assertEqual(template.region.left, 10)
            self.assertEqual(template.region.top, 20)
            self.assertEqual(template.region.right, 110)
            self.assertEqual(template.region.bottom, 220)

    def test_template_region_must_be_complete(self):
        from dbl_farm_bot.gui import FarmBotApp

        app = _template_app(Path("config.json"))
        app.template_region_bottom.set("")

        with self.assertRaisesRegex(ValueError, "Fill all region fields"):
            app._template_from_fields()


class _Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _template_app(config_path: Path):
    from dbl_farm_bot.gui import FarmBotApp

    app = FarmBotApp.__new__(FarmBotApp)
    app.config_path = _Var(str(config_path))
    app.template_name = _Var("victory")
    app.template_path = _Var("templates/victory.png")
    app.template_threshold = _Var("0.91")
    app.template_stride = _Var("2")
    app.template_region_left = _Var("10")
    app.template_region_top = _Var("20")
    app.template_region_right = _Var("110")
    app.template_region_bottom = _Var("220")
    app.messages = []
    app._log = app.messages.append
    return app


if __name__ == "__main__":
    unittest.main()
