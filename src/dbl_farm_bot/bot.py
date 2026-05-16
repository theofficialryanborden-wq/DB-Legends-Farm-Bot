from __future__ import annotations

from dataclasses import dataclass, field
import time

from .battle import BattleAutomator, BattleDetector, BattleResult, ScreenshotBattleDetector
from .config import BotConfig, NavigationStep
from .device import Device
from .vision import ScreenAnalyzer


@dataclass(frozen=True)
class FarmCycleResult:
    cycle: int
    battle: BattleResult


@dataclass(frozen=True)
class FarmResult:
    cycles: list[FarmCycleResult] = field(default_factory=list)


class MenuNavigator:
    def __init__(self, device: Device, analyzer: ScreenAnalyzer, now=time.monotonic) -> None:
        self.device = device
        self.analyzer = analyzer
        self.now = now

    def run(self, steps: list[NavigationStep]) -> None:
        for step in steps:
            for _ in range(step.retries):
                self._wait_for_template(step)
                self.device.tap(step.tap)
                self.device.sleep(step.wait_after)

    def _wait_for_template(self, step: NavigationStep) -> None:
        if not step.wait_for_template:
            return
        started_at = self.now()
        while self.now() - started_at < step.timeout:
            image = self.analyzer.image_from_png(self.device.screenshot())
            if self.analyzer.find_template(image, step.wait_for_template):
                return
            self.device.sleep(0.25)
        raise TimeoutError(f"Timed out waiting for template {step.wait_for_template!r}")


class DragonBallLegendsBot:
    def __init__(
        self,
        device: Device,
        config: BotConfig,
        analyzer: ScreenAnalyzer | None = None,
        detector: BattleDetector | None = None,
        now=time.monotonic,
    ) -> None:
        self.device = device
        self.config = config
        self.analyzer = analyzer or ScreenAnalyzer(config.templates)
        self.detector = detector or ScreenshotBattleDetector(device, self.analyzer)
        self.now = now

    def farm_events(self, cycles: int | None = None) -> FarmResult:
        total_cycles = cycles if cycles is not None else self.config.cycles
        navigator = MenuNavigator(self.device, self.analyzer, self.now)
        results: list[FarmCycleResult] = []

        for cycle in range(1, total_cycles + 1):
            navigator.run(self.config.enter_event_steps)
            battle = BattleAutomator(
                self.device,
                self.detector,
                self.config.battle,
                self.now,
            ).run()
            results.append(FarmCycleResult(cycle, battle))
            navigator.run(self.config.post_battle_steps)
            if cycle < total_cycles:
                self.device.sleep(self.config.loop_delay)

        return FarmResult(results)
