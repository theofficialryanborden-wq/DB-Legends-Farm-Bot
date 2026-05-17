from __future__ import annotations

from dataclasses import replace
import argparse
from pathlib import Path
from queue import Queue
import sys
from threading import Thread
import traceback

from .bot import DragonBallLegendsBot
from .cli import NoopBattleDetector, _format_result
from .config import BotConfig
from .device import ADBDevice, DryRunDevice


class FarmBotApp:
    def __init__(self, root) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.queue: Queue[str] = Queue()
        self.running = False

        root.title("DB Legends Farm Bot")
        root.geometry("760x560")

        frame = ttk.Frame(root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(8, weight=1)

        self.config_path = tk.StringVar(value="dbl_pixel9a_config.json")
        self.cycles = tk.StringVar(value="1")
        self.serial = tk.StringVar(value="")
        self.adb_path = tk.StringVar(value="adb")
        self.max_battle_seconds = tk.StringVar(value="")
        self.dry_run = tk.BooleanVar(value=True)

        self._entry(frame, "Config file", self.config_path, 0)
        self._entry(frame, "Cycles", self.cycles, 1)
        self._entry(frame, "ADB serial", self.serial, 2)
        self._entry(frame, "ADB path", self.adb_path, 3)
        self._entry(frame, "Max battle seconds", self.max_battle_seconds, 4)

        ttk.Checkbutton(frame, text="Dry run", variable=self.dry_run).grid(
            row=5, column=1, sticky="w", pady=4
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(
            buttons,
            text="Write Pixel 9a config",
            command=self.write_default_config,
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Run bot", command=self.run_bot).grid(row=0, column=1)

        self.status = tk.StringVar(value="Ready. Dry run is enabled by default.")
        ttk.Label(frame, textvariable=self.status).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.output = tk.Text(frame, height=18, wrap="word")
        self.output.grid(row=8, column=0, columnspan=2, sticky="nsew")
        self.output.insert(
            "end",
            "Pixel 9a defaults target 1080x2424 portrait mode.\n"
            "Turn off Dry run only after adb devices shows your phone/emulator.\n",
        )
        root.after(100, self._drain_queue)

    def _entry(self, frame, label: str, variable, row: int) -> None:
        from tkinter import ttk

        ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=variable).grid(
            row=row, column=1, sticky="ew", pady=4
        )

    def write_default_config(self) -> None:
        path = Path(self.config_path.get()).expanduser()
        BotConfig().save(path)
        self._log(f"Wrote Pixel 9a config to {path}")

    def run_bot(self) -> None:
        if self.running:
            self._log("Bot is already running.")
            return
        self.running = True
        self.status.set("Running...")
        Thread(target=self._run_bot_worker, daemon=True).start()

    def _run_bot_worker(self) -> None:
        try:
            config = self._load_config()
            if self.dry_run.get():
                device = DryRunDevice()
                bot = DragonBallLegendsBot(
                    device,
                    config,
                    detector=NoopBattleDetector(),
                    now=device.now,
                )
                result = bot.farm_events()
                self.queue.put(_format_result(result.cycles))
                self.queue.put("\n".join(device.actions))
            else:
                device = ADBDevice(config.device_serial, adb_path=self.adb_path.get())
                result = DragonBallLegendsBot(device, config).farm_events()
                self.queue.put(_format_result(result.cycles))
        except Exception:
            self.queue.put(traceback.format_exc())
        finally:
            self.queue.put("__DONE__")

    def _load_config(self) -> BotConfig:
        path = Path(self.config_path.get()).expanduser()
        config = BotConfig.load(path) if path.exists() else BotConfig()
        config = replace(config, cycles=max(1, int(self.cycles.get() or "1")))
        serial = self.serial.get().strip()
        if serial:
            config = replace(config, device_serial=serial)
        max_battle_seconds = self.max_battle_seconds.get().strip()
        if max_battle_seconds:
            config = replace(
                config,
                battle=replace(config.battle, battle_timeout=float(max_battle_seconds)),
            )
        return config

    def _drain_queue(self) -> None:
        while not self.queue.empty():
            message = self.queue.get()
            if message == "__DONE__":
                self.running = False
                self.status.set("Finished.")
            else:
                self._log(message)
        self.root.after(100, self._drain_queue)

    def _log(self, message: str) -> None:
        self.output.insert("end", message.rstrip() + "\n")
        self.output.see("end")


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Open the Dragon Ball Legends farming bot desktop GUI."
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)

    try:
        import tkinter as tk
    except ModuleNotFoundError:
        print(
            "Tkinter is required for the GUI. On Windows/macOS it normally ships "
            "with Python. On Debian/Ubuntu install it with: sudo apt install python3-tk",
            file=sys.stderr,
        )
        return 1

    root = tk.Tk()
    FarmBotApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
