from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


DEFAULT_DEVICE_PROFILE = "google_pixel_9a_1080x2424"


@dataclass(frozen=True)
class Point:
    x: int
    y: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Point":
        return cls(x=int(data["x"]), y=int(data["y"]))


@dataclass(frozen=True)
class Region:
    left: int
    top: int
    right: int
    bottom: int

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Region | None":
        if data is None:
            return None
        return cls(
            left=int(data["left"]),
            top=int(data["top"]),
            right=int(data["right"]),
            bottom=int(data["bottom"]),
        )


@dataclass(frozen=True)
class NavigationStep:
    name: str
    tap: Point
    wait_after: float = 1.0
    retries: int = 1
    wait_for_template: str | None = None
    timeout: float = 8.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NavigationStep":
        return cls(
            name=str(data["name"]),
            tap=Point.from_dict(data["tap"]),
            wait_after=float(data.get("wait_after", 1.0)),
            retries=int(data.get("retries", 1)),
            wait_for_template=data.get("wait_for_template"),
            timeout=float(data.get("timeout", 8.0)),
        )


@dataclass(frozen=True)
class TemplateConfig:
    name: str
    path: str
    threshold: float = 0.88
    region: Region | None = None
    stride: int = 4

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemplateConfig":
        return cls(
            name=str(data["name"]),
            path=str(data["path"]),
            threshold=float(data.get("threshold", 0.88)),
            region=Region.from_dict(data.get("region")),
            stride=max(1, int(data.get("stride", 4))),
        )


@dataclass(frozen=True)
class BattleConfig:
    arts_cards: list[Point] = field(
        default_factory=lambda: [
            Point(360, 2310),
            Point(570, 2310),
            Point(780, 2310),
            Point(990, 2310),
        ]
    )
    rising_rush_button: Point = Point(955, 1988)
    rising_rush_pick_card: Point = Point(360, 2310)
    rising_rush_available_region: Region | None = Region(875, 1887, 1035, 2089)
    rising_rush_min_brightness: float = 95.0
    timing_gauge_region: Region | None = Region(215, 1250, 865, 1338)
    timing_perfect_x_ratio: float = 0.94
    timing_tolerance_px: int = 18
    timing_poll_interval: float = 0.025
    timing_timeout: float = 2.5
    timing_fallback_delay: float = 1.25
    arts_card_cooldown: float = 0.16
    battle_poll_interval: float = 0.25
    battle_timeout: float = 180.0
    victory_template: str | None = None
    defeat_template: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BattleConfig":
        defaults = cls()
        return cls(
            arts_cards=[
                Point.from_dict(point)
                for point in data.get("arts_cards", [asdict(point) for point in defaults.arts_cards])
            ],
            rising_rush_button=Point.from_dict(
                data.get("rising_rush_button", asdict(defaults.rising_rush_button))
            ),
            rising_rush_pick_card=Point.from_dict(
                data.get("rising_rush_pick_card", asdict(defaults.rising_rush_pick_card))
            ),
            rising_rush_available_region=Region.from_dict(
                data.get("rising_rush_available_region", asdict(defaults.rising_rush_available_region))
            ),
            rising_rush_min_brightness=float(
                data.get("rising_rush_min_brightness", defaults.rising_rush_min_brightness)
            ),
            timing_gauge_region=Region.from_dict(
                data.get("timing_gauge_region", asdict(defaults.timing_gauge_region))
            ),
            timing_perfect_x_ratio=float(
                data.get("timing_perfect_x_ratio", defaults.timing_perfect_x_ratio)
            ),
            timing_tolerance_px=int(data.get("timing_tolerance_px", defaults.timing_tolerance_px)),
            timing_poll_interval=float(
                data.get("timing_poll_interval", defaults.timing_poll_interval)
            ),
            timing_timeout=float(data.get("timing_timeout", defaults.timing_timeout)),
            timing_fallback_delay=float(
                data.get("timing_fallback_delay", defaults.timing_fallback_delay)
            ),
            arts_card_cooldown=float(data.get("arts_card_cooldown", defaults.arts_card_cooldown)),
            battle_poll_interval=float(data.get("battle_poll_interval", defaults.battle_poll_interval)),
            battle_timeout=float(data.get("battle_timeout", defaults.battle_timeout)),
            victory_template=data.get("victory_template", defaults.victory_template),
            defeat_template=data.get("defeat_template", defaults.defeat_template),
        )


@dataclass(frozen=True)
class BotConfig:
    device_profile: str = DEFAULT_DEVICE_PROFILE
    device_serial: str | None = None
    templates: list[TemplateConfig] = field(default_factory=list)
    enter_event_steps: list[NavigationStep] = field(
        default_factory=lambda: [
            NavigationStep("events", Point(920, 2247), 1.5),
            NavigationStep("recommended", Point(310, 461), 1.0),
            NavigationStep("first_event", Point(560, 871), 1.0),
            NavigationStep("battle", Point(900, 2323), 1.0),
            NavigationStep("start", Point(900, 2323), 2.5),
        ]
    )
    post_battle_steps: list[NavigationStep] = field(
        default_factory=lambda: [
            NavigationStep("results_next", Point(900, 2323), 1.5, retries=3),
            NavigationStep("rematch", Point(900, 2323), 2.0),
        ]
    )
    battle: BattleConfig = field(default_factory=BattleConfig)
    cycles: int = 1
    loop_delay: float = 1.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BotConfig":
        return cls(
            device_profile=data.get("device_profile", DEFAULT_DEVICE_PROFILE),
            device_serial=data.get("device_serial"),
            templates=[TemplateConfig.from_dict(item) for item in data.get("templates", [])],
            enter_event_steps=[
                NavigationStep.from_dict(item) for item in data.get("enter_event_steps", [])
            ]
            or cls().enter_event_steps,
            post_battle_steps=[
                NavigationStep.from_dict(item) for item in data.get("post_battle_steps", [])
            ]
            or cls().post_battle_steps,
            battle=BattleConfig.from_dict(data.get("battle", {})),
            cycles=int(data.get("cycles", 1)),
            loop_delay=float(data.get("loop_delay", 1.0)),
        )

    @classmethod
    def load(cls, path: Path) -> "BotConfig":
        with path.open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def save(self, path: Path) -> None:
        path.write_text(self.to_json() + "\n", encoding="utf-8")
