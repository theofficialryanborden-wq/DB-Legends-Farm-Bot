from __future__ import annotations

from dataclasses import dataclass, field
import subprocess
import time
from typing import Protocol

from .config import Point


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

    def _run_shell(self, *args: str) -> bytes:
        return self._run("shell", *args)

    def _run(self, *args: str) -> bytes:
        command = [self.adb_path]
        if self.serial:
            command.extend(["-s", self.serial])
        command.extend(args)
        return subprocess.check_output(command)


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
