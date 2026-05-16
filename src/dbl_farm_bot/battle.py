from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Protocol

from .config import BattleConfig, Point
from .device import Device
from .vision import ScreenAnalyzer


class BattleDetector(Protocol):
    def rising_rush_available(self, config: BattleConfig) -> bool:
        ...

    def template_visible(self, name: str | None) -> bool:
        ...

    def timing_marker_x(self, config: BattleConfig) -> int | None:
        ...


class ScreenshotBattleDetector:
    def __init__(self, device: Device, analyzer: ScreenAnalyzer) -> None:
        self.device = device
        self.analyzer = analyzer

    def rising_rush_available(self, config: BattleConfig) -> bool:
        if config.rising_rush_available_region is None:
            return False
        image = self._screenshot_image()
        brightness = self.analyzer.average_brightness(image, config.rising_rush_available_region)
        return brightness >= config.rising_rush_min_brightness

    def template_visible(self, name: str | None) -> bool:
        if not name:
            return False
        image = self._screenshot_image()
        return self.analyzer.find_template(image, name) is not None

    def timing_marker_x(self, config: BattleConfig) -> int | None:
        if config.timing_gauge_region is None:
            return None
        image = self._screenshot_image()
        return self.analyzer.brightest_column_x(image, config.timing_gauge_region)

    def _screenshot_image(self):
        return self.analyzer.image_from_png(self.device.screenshot())


@dataclass(frozen=True)
class BattleResult:
    status: str
    rising_rush_used: bool
    perfect_rising_rush_attempted: bool


class BattleAutomator:
    def __init__(
        self,
        device: Device,
        detector: BattleDetector,
        config: BattleConfig,
        now=time.monotonic,
    ) -> None:
        self.device = device
        self.detector = detector
        self.config = config
        self.now = now

    def run(self) -> BattleResult:
        started_at = self.now()
        rising_rush_used = False
        perfect_rising_rush_attempted = False

        while self.now() - started_at < self.config.battle_timeout:
            if self.detector.template_visible(self.config.victory_template):
                return BattleResult("victory", rising_rush_used, perfect_rising_rush_attempted)
            if self.detector.template_visible(self.config.defeat_template):
                return BattleResult("defeat", rising_rush_used, perfect_rising_rush_attempted)

            if not rising_rush_used and self.detector.rising_rush_available(self.config):
                perfect_rising_rush_attempted = self._perform_rising_rush()
                rising_rush_used = True
            else:
                self._play_arts_cards()

            self.device.sleep(self.config.battle_poll_interval)

        return BattleResult("timeout", rising_rush_used, perfect_rising_rush_attempted)

    def _play_arts_cards(self) -> None:
        for card in self.config.arts_cards:
            self.device.tap(card)
            self.device.sleep(self.config.arts_card_cooldown)

    def _perform_rising_rush(self) -> bool:
        self.device.tap(self.config.rising_rush_button)
        self.device.sleep(0.35)
        self.device.tap(self.config.rising_rush_pick_card)
        self.device.sleep(0.35)
        return self._time_max_rising_rush()

    def _time_max_rising_rush(self) -> bool:
        region = self.config.timing_gauge_region
        if region is None:
            self.device.sleep(self.config.timing_fallback_delay)
            self.device.tap(self.config.rising_rush_pick_card)
            return False

        target_x = int(region.left + (region.right - region.left) * self.config.timing_perfect_x_ratio)
        target_y = int((region.top + region.bottom) / 2)
        started_at = self.now()

        while self.now() - started_at < self.config.timing_timeout:
            marker_x = self.detector.timing_marker_x(self.config)
            if marker_x is not None and abs(marker_x - target_x) <= self.config.timing_tolerance_px:
                self.device.tap(Point(target_x, target_y))
                return True
            self.device.sleep(self.config.timing_poll_interval)

        self.device.sleep(self.config.timing_fallback_delay)
        self.device.tap(Point(target_x, target_y))
        return False
