# DB-Legends-Farm-Bot
Farm Dragon Ball Legends events for event rewards.

## What it does

This project provides an ADB-driven Dragon Ball Legends farming bot. It can:

- Navigate a configurable event-entry flow through menu taps.
- Start event battles and cycle arts cards so the character keeps attacking.
- Detect Rising Rush availability from the configured button region.
- Fire Rising Rush, pick an arts card, and time the strike by watching the Rising Rush timing gauge.
- Repeat the event loop for a configured number of cycles.

The defaults target a 1080x1920 portrait Android device or emulator. Use the generated JSON config to tune coordinates for your device.

## Setup

Install the package in a Python 3.11+ environment:

`python -m pip install -e .`

Make sure Android Debug Bridge can see your device:

`adb devices`

## Configure

Write the default config:

`dbl-farm-bot --write-default-config dbl_config.json`

Tune these important fields in `dbl_config.json`:

- `enter_event_steps`: menu taps to open the desired event and start the battle.
- `post_battle_steps`: result-screen and rematch taps after a battle.
- `battle.arts_cards`: the four arts card slot centers.
- `battle.rising_rush_button`: Rising Rush button center.
- `battle.rising_rush_available_region`: area sampled to decide whether Rising Rush is ready.
- `battle.timing_gauge_region`: timing gauge bounds used for the maximum Rising Rush tap.
- `battle.timing_perfect_x_ratio`: target location on the gauge, defaulting near the far-right perfect zone.

## Run

Dry-run the tap sequence without touching a device:

`dbl-farm-bot --dry-run --cycles 1 --max-battle-seconds 1`

Run against the active ADB device:

`dbl-farm-bot --config dbl_config.json --cycles 10`

Run against a specific device:

`dbl-farm-bot --config dbl_config.json --serial emulator-5554 --cycles 10`

## Notes

Screen detection uses screenshots from `adb exec-out screencap -p` and Pillow. If the bot misses taps, update the config coordinates for your emulator resolution before long farming runs.
