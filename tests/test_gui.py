import unittest


class GuiTest(unittest.TestCase):
    def test_gui_module_imports_without_opening_window(self):
        from dbl_farm_bot import gui

        self.assertTrue(callable(gui.main))


if __name__ == "__main__":
    unittest.main()
