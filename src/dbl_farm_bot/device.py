from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import time
from typing import Protocol

from .config import Point


class ADBError(RuntimeError):
    """Raised when ADB cannot be launched or cannot reach a usable device."""


class Device(Protocol):
    def tap(self, point: Point) -> None:
        ...

    def swipe(self, start: Point, end: Point, duration_ms: int = 300) -> None:
        ...

    def sleep(self, seconds: float) -> None:
        ...

    def screenshot(self) -> bytes:
        ...


class ADBDevice:
    def __init__(self, serial: str | None = None, adb_path: str = "adb") -> None:
        self.serial = serial
        self.adb_path = adb_path

    def tap(self, point: Point) -> None:
        self._run_shell("input", "tap", str(point.x), str(point.y))

    def swipe(self, start: Point, end: Point, duration_ms: int = 300) -> None:
        self._run_shell(
            "input",
            "swipe",
            str(start.x),
            str(start.y),
            str(end.x),
            str(end.y),
            str(duration_ms),
        )

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def screenshot(self) -> bytes:
        return self._run("exec-out", "screencap", "-p")

    def check_connection(self) -> str:
        output = self._execute([self.adb_path, "devices"]).decode(
            "utf-8", errors="replace"
        )
        devices = [
            line.split()[0]
            for line in output.splitlines()[1:]
            if line.strip().endswith("\tdevice")
        ]
        if self.serial:
            if self.serial not in devices:
                raise ADBError(
                    f"ADB is working, but serial {self.serial!r} is not listed as a ready device.\n\n"
                    f"adb devices output:\n{output.strip()}"
                )
        elif not devices:
            raise ADBError(
                "ADB is working, but no ready Android device is listed.\n\n"
                "On your PC, enable USB debugging or start your emulator, then run "
                "`adb devices` and accept the authorization prompt on the phone."
            )
        return output

    def _run_shell(self, *args: str) -> bytes:
        return self._run("shell", *args)

    def _run(self, *args: str) -> bytes:
        command = [self.adb_path]
        if self.serial:
            command.extend(["-s", self.serial])
        command.extend(args)
        return self._execute(command)

    def _execute(self, command: list[str]) -> bytes:
        self._validate_adb_path()
        try:
            return subprocess.check_output(command, stderr=subprocess.STDOUT)
        except PermissionError as exc:
            raise ADBError(
                f"Windows denied permission to run ADB at {self.adb_path!r}.\n\n"
                "Set the GUI's ADB path to the full adb.exe file path, for example:\n"
                r"C:\Users\YOUR_NAME\AppData\Local\Android\Sdk\platform-tools\adb.exe"
                "\n\nDo not set it to the platform-tools folder itself."
            ) from exc
        except FileNotFoundError as exc:
            raise ADBError(
                f"ADB was not found at {self.adb_path!r}.\n\n"
                "Install Android Platform Tools, then set the GUI's ADB path to adb.exe "
                "or add platform-tools to your PATH."
            ) from exc
        except subprocess.CalledProcessError as exc:
            output = exc.output.decode("utf-8", errors="replace").strip()
            raise ADBError(
                f"ADB command failed with exit code {exc.returncode}.\n\n{output}"
            ) from exc

    def _validate_adb_path(self) -> None:
        path = Path(self.adb_path)
        if path.is_dir():
            raise ADBError(
                f"ADB path points to a folder, not adb.exe: {self.adb_path!r}\n\n"
                "Set it to the full adb.exe file path, for example:\n"
                r"C:\Users\YOUR_NAME\AppData\Local\Android\Sdk\platform-tools\adb.exe"
            )


@dataclass
class DryRunDevice:
    screenshot_bytes: bytes = b""
    actions: list[str] = field(default_factory=list)
    elapsed: float = 0.0

    def tap(self, point: Point) -> None:
        self.actions.append(f"tap {point.x} {point.y}")

    def swipe(self, start: Point, end: Point, duration_ms: int = 300) -> None:
        self.actions.append(
            f"swipe {start.x} {start.y} {end.x} {end.y} {duration_ms}"
        )

    def sleep(self, seconds: float) -> None:
        self.actions.append(f"sleep {seconds:.3f}")
        self.elapsed += seconds

    def screenshot(self) -> bytes:
        self.actions.append("screenshot")
        return self.screenshot_bytes

    def now(self) -> float:
        return self.elapsed
