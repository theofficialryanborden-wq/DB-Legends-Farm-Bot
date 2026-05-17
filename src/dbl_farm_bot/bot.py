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


class NavigationError(RuntimeError):
    pass


class MenuNavigator:
    def __init__(
        self,
        device: Device,
        analyzer: ScreenAnalyzer,
        allow_blind_taps: bool = False,
        now=time.monotonic,
    ) -> None:
        self.device = device
        self.analyzer = analyzer
        self.allow_blind_taps = allow_blind_taps
        self.now = now

    def run(self, steps: list[NavigationStep]) -> None:
        for step in steps:
            for _ in range(step.retries):
                tap_point = self._resolve_tap_point(step)
                self.device.tap(tap_point)
                self.device.sleep(step.wait_after)

    def _resolve_tap_point(self, step: NavigationStep):
        if step.tap_template:
            match = self._wait_for_template(step.tap_template, step.timeout)
            return match.point
        if step.wait_for_template:
            self._wait_for_template(step.wait_for_template, step.timeout)
        if step.tap and self.allow_blind_taps:
            return step.tap
        if step.tap:
            raise NavigationError(
                f"Refusing blind tap for menu step {step.name!r} at {step.tap.x},{step.tap.y}.\n\n"
                "Real device runs now require image templates so the bot only taps recognized "
                "Dragon Ball Legends UI. Add a template for this step or set "
                "`allow_blind_menu_taps` to true only after calibrating your screen."
            )
        raise NavigationError(f"Menu step {step.name!r} has no tap target configured.")

    def _wait_for_template(self, template_name: str, timeout: float):
        if not self.analyzer.has_template(template_name):
            raise NavigationError(
                f"Template {template_name!r} is not configured.\n\n"
                "Add it to the config's `templates` list with a screenshot crop of the matching "
                "button/text, or enable dry run to preview coordinates only."
            )
        started_at = self.now()
        while self.now() - started_at < timeout:
            image = self.analyzer.image_from_png(self.device.screenshot())
            match = self.analyzer.find_template(image, template_name)
            if match:
                return match
            self.device.sleep(0.25)
        raise NavigationError(f"Timed out waiting for template {template_name!r}")


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
        navigator = MenuNavigator(
            self.device,
            self.analyzer,
            allow_blind_taps=self.config.allow_blind_menu_taps,
            now=self.now,
        )
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
