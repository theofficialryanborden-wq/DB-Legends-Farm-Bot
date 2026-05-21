# DB-Legends-Farm-Bot
Farm Dragon Ball Legends events for event rewards.

## What it does

This project provides an ADB-driven Dragon Ball Legends farming bot. It can:

- Navigate a configurable event-entry flow through menu taps.
- Start event battles and cycle arts cards so the character keeps attacking.
- Detect Rising Rush availability from the configured button region.
- Fire Rising Rush, pick an arts card, and time the strike by watching the Rising Rush timing gauge.
- Repeat the event loop for a configured number of cycles.

The defaults target a Google Pixel 9a in 1080x2424 portrait mode. Use the generated JSON config to tune coordinates if your Android display size, emulator skin, or in-game layout differs.

## Setup

Install the package in a Python 3.11+ environment:

`python -m pip install -e .`

Make sure Android Debug Bridge can see your device:

`adb devices`

On Windows, set the GUI's `ADB path` to the full `adb.exe` file if plain `adb` does not work. A common Android Studio path is:

`C:\Users\YOUR_NAME\AppData\Local\Android\Sdk\platform-tools\adb.exe`

Do not set `ADB path` to the `platform-tools` folder.

## Configure

Write the default config:

`dbl-farm-bot --write-default-config dbl_config.json`

Or open the desktop GUI:

`dbl-farm-bot-gui`

If your script folder is not on `PATH`, run the GUI as a Python module instead:

`python -m dbl_farm_bot.gui`

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

GUI dry run:

1. Run `dbl-farm-bot-gui`.
2. Leave `Dry run` checked.
3. Click `Write Pixel 9a config`.
4. Click `Run bot`.

GUI template setup:

1. Set `Config file` to the JSON config you want to edit.
2. Fill in the template `Name`, image `Path`, `Threshold`, and `Stride`.
3. Optionally fill all four `Region` fields to limit matching to one screen area.
4. Click `Add template` to save the template into the config file.
5. Click `Load templates` to review the templates currently saved in that config.

Run against the active ADB device:

`dbl-farm-bot --config dbl_config.json --cycles 10`

Run against a specific device:

`dbl-farm-bot --config dbl_config.json --serial emulator-5554 --cycles 10`

GUI device run:

1. Run `adb devices` and confirm your Pixel 9a or emulator is listed.
2. Open `dbl-farm-bot-gui`.
3. Set `ADB path` to `adb` or the full `adb.exe` path.
4. Click `Test ADB`.
5. Set `Config file` to your Pixel 9a config.
6. Set `ADB serial` if more than one device is listed.
7. Uncheck `Dry run`.
8. Click `Run bot`.

## Notes

Screen detection uses screenshots from `adb exec-out screencap -p` and Pillow. If the bot misses taps, update the config coordinates for your emulator resolution before long farming runs.
