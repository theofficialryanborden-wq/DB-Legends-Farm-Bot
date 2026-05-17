from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .battle import BattleDetector
from .bot import DragonBallLegendsBot
from .config import BattleConfig, BotConfig
from .device import ADBDevice, DryRunDevice


class NoopBattleDetector:
    def rising_rush_available(self, config: BattleConfig) -> bool:
        return False

    def template_visible(self, name: str | None) -> bool:
        return False

    def timing_marker_x(self, config: BattleConfig) -> int | None:
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Farm Dragon Ball Legends events through ADB automation."
    )
    parser.add_argument("--config", type=Path, help="Path to a bot JSON configuration.")
    parser.add_argument("--cycles", type=int, help="Number of farming cycles to run.")
    parser.add_argument("--serial", help="ADB device serial. Overrides config device_serial.")
    parser.add_argument("--adb-path", default="adb", help="ADB executable path.")
    parser.add_argument("--dry-run", action="store_true", help="Print taps without touching a device.")
    parser.add_argument(
        "--allow-blind-menu-taps",
        action="store_true",
        help="Allow coordinate-only menu taps. Use only after calibrating your screen.",
    )
    parser.add_argument(
        "--max-battle-seconds",
        type=float,
        help="Override battle timeout for quick smoke tests or safer first runs.",
    )
    parser.add_argument(
        "--print-default-config",
        action="store_true",
        help="Print the default JSON configuration and exit.",
    )
    parser.add_argument(
        "--write-default-config",
        type=Path,
        help="Write the default JSON configuration to this path and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.print_default_config:
        print(BotConfig().to_json())
        return 0

    if args.write_default_config:
        BotConfig().save(args.write_default_config)
        print(f"Wrote {args.write_default_config}")
        return 0

    config = BotConfig.load(args.config) if args.config else BotConfig()
    if args.cycles is not None:
        config = replace(config, cycles=args.cycles)
    if args.serial:
        config = replace(config, device_serial=args.serial)
    if args.max_battle_seconds is not None:
        config = replace(
            config,
            battle=replace(config.battle, battle_timeout=args.max_battle_seconds),
        )
    if args.allow_blind_menu_taps:
        config = replace(config, allow_blind_menu_taps=True)

    if args.dry_run:
        config = replace(config, allow_blind_menu_taps=True)
        device = DryRunDevice()
        bot = DragonBallLegendsBot(
            device,
            config,
            detector=NoopBattleDetector(),
            now=device.now,
        )
        result = bot.farm_events()
        print(_format_result(result.cycles))
        print("\n".join(device.actions))
        return 0

    device = ADBDevice(config.device_serial, adb_path=args.adb_path)
    bot = DragonBallLegendsBot(device, config)
    result = bot.farm_events()
    print(_format_result(result.cycles))
    return 0


def _format_result(cycles) -> str:
    lines = ["Farm run complete:"]
    for cycle in cycles:
        lines.append(
            "cycle "
            f"{cycle.cycle}: status={cycle.battle.status}, "
            f"rising_rush_used={cycle.battle.rising_rush_used}, "
            f"perfect_attempted={cycle.battle.perfect_rising_rush_attempted}"
        )
    return "\n".join(lines)
