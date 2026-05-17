import tempfile
import unittest
from unittest.mock import patch

from dbl_farm_bot.config import Point
from dbl_farm_bot.device import ADBDevice, ADBError


class ADBDeviceTest(unittest.TestCase):
    def test_rejects_adb_path_that_points_to_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ADBError, "folder, not adb.exe"):
                ADBDevice(adb_path=directory).check_connection()

    def test_wraps_windows_permission_error_with_adb_hint(self):
        with patch(
            "subprocess.check_output",
            side_effect=PermissionError(5, "Access is denied", "adb"),
        ):
            with self.assertRaisesRegex(ADBError, "full adb.exe file path"):
                ADBDevice(adb_path="adb").tap(Point(1, 2))

    def test_check_connection_requires_ready_device(self):
        output = b"List of devices attached\nemulator-5554\toffline\n"
        with patch("subprocess.check_output", return_value=output):
            with self.assertRaisesRegex(ADBError, "no ready Android device"):
                ADBDevice(adb_path="adb").check_connection()

if __name__ == "__main__":
    unittest.main()
