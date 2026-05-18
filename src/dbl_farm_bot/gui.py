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
from .config import BotConfig, Region, TemplateConfig
from .device import ADBDevice, ADBError, DryRunDevice


class FarmBotApp:
    def __init__(self, root) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.root = root
        self.queue: Queue[str] = Queue()
        self.running = False

        root.title("DB Legends Farm Bot")
        root.geometry("860x720")

        frame = ttk.Frame(root, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(9, weight=1)

        self.config_path = tk.StringVar(value="dbl_pixel9a_config.json")
        self.cycles = tk.StringVar(value="1")
        self.serial = tk.StringVar(value="")
        self.adb_path = tk.StringVar(value="adb")
        self.max_battle_seconds = tk.StringVar(value="")
        self.dry_run = tk.BooleanVar(value=True)
        self.template_name = tk.StringVar(value="")
        self.template_path = tk.StringVar(value="")
        self.template_threshold = tk.StringVar(value="0.88")
        self.template_stride = tk.StringVar(value="4")
        self.template_region_left = tk.StringVar(value="")
        self.template_region_top = tk.StringVar(value="")
        self.template_region_right = tk.StringVar(value="")
        self.template_region_bottom = tk.StringVar(value="")

        self._entry(frame, "Config file", self.config_path, 0)
        self._entry(frame, "Cycles", self.cycles, 1)
        self._entry(frame, "ADB serial", self.serial, 2)
        self._entry(frame, "ADB path", self.adb_path, 3)
        self._entry(frame, "Max battle seconds", self.max_battle_seconds, 4)

        ttk.Checkbutton(frame, text="Dry run", variable=self.dry_run).grid(
            row=5, column=1, sticky="w", pady=4
        )

        self._templates_section(frame, 6)

        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(
            buttons,
            text="Write Pixel 9a config",
            command=self.write_default_config,
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Test ADB", command=self.test_adb).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(buttons, text="Run bot", command=self.run_bot).grid(row=0, column=2)

        self.status = tk.StringVar(value="Ready. Dry run is enabled by default.")
        ttk.Label(frame, textvariable=self.status).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.output = tk.Text(frame, height=18, wrap="word")
        self.output.grid(row=9, column=0, columnspan=2, sticky="nsew")
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

    def _templates_section(self, frame, row: int) -> None:
        from tkinter import ttk

        section = ttk.LabelFrame(frame, text="Templates", padding=8)
        section.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        section.columnconfigure(1, weight=1)
        section.columnconfigure(3, weight=1)

        ttk.Label(section, text="Name").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(section, textvariable=self.template_name).grid(
            row=0, column=1, sticky="ew", pady=3, padx=(4, 12)
        )
        ttk.Label(section, text="Path").grid(row=0, column=2, sticky="w", pady=3)
        path_frame = ttk.Frame(section)
        path_frame.grid(row=0, column=3, sticky="ew", pady=3)
        path_frame.columnconfigure(0, weight=1)
        ttk.Entry(path_frame, textvariable=self.template_path).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(path_frame, text="Browse", command=self.browse_template).grid(
            row=0, column=1, padx=(4, 0)
        )

        ttk.Label(section, text="Threshold").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(section, textvariable=self.template_threshold, width=8).grid(
            row=1, column=1, sticky="w", pady=3, padx=(4, 12)
        )
        ttk.Label(section, text="Stride").grid(row=1, column=2, sticky="w", pady=3)
        ttk.Entry(section, textvariable=self.template_stride, width=8).grid(
            row=1, column=3, sticky="w", pady=3
        )

        region = ttk.Frame(section)
        region.grid(row=2, column=0, columnspan=4, sticky="ew", pady=3)
        ttk.Label(region, text="Region (optional)").grid(row=0, column=0, sticky="w")
        for index, (label, variable) in enumerate(
            [
                ("Left", self.template_region_left),
                ("Top", self.template_region_top),
                ("Right", self.template_region_right),
                ("Bottom", self.template_region_bottom),
            ],
            start=1,
        ):
            ttk.Label(region, text=label).grid(row=0, column=index * 2 - 1, padx=(8, 2))
            ttk.Entry(region, textvariable=variable, width=7).grid(row=0, column=index * 2)

        template_buttons = ttk.Frame(section)
        template_buttons.grid(row=3, column=0, columnspan=4, sticky="w", pady=(6, 0))
        ttk.Button(template_buttons, text="Load templates", command=self.load_templates).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(template_buttons, text="Add template", command=self.add_template).grid(
            row=0, column=1
        )

    def write_default_config(self) -> None:
        path = Path(self.config_path.get()).expanduser()
        BotConfig().save(path)
        self._log(f"Wrote Pixel 9a config to {path}")

    def browse_template(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="Select template image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.template_path.set(path)

    def load_templates(self) -> None:
        try:
            config = self._load_config_file()
            self._log_template_summary(config)
        except Exception:
            self._log(traceback.format_exc())

    def add_template(self) -> None:
        try:
            path = Path(self.config_path.get()).expanduser()
            config = self._load_config_file()
            template = self._template_from_fields()
            config = replace(config, templates=[*config.templates, template])
            config.save(path)
            self._log(f"Added template {template.name!r} to {path}")
            self._log_template_summary(config)
            self._clear_template_fields()
        except Exception:
            self._log(traceback.format_exc())

    def run_bot(self) -> None:
        if self.running:
            self._log("Bot is already running.")
            return
        self.running = True
        self.status.set("Running...")
        Thread(target=self._run_bot_worker, daemon=True).start()

    def test_adb(self) -> None:
        if self.running:
            self._log("Bot is already running.")
            return
        self.running = True
        self.status.set("Testing ADB...")
        Thread(target=self._test_adb_worker, daemon=True).start()

    def _test_adb_worker(self) -> None:
        try:
            config = self._load_config()
            output = ADBDevice(config.device_serial, adb_path=self.adb_path.get()).check_connection()
            self.queue.put("ADB connection OK:\n" + output.strip())
        except ADBError as exc:
            self.queue.put(str(exc))
        except Exception:
            self.queue.put(traceback.format_exc())
        finally:
            self.queue.put("__DONE__")

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
                self.queue.put("Checking ADB connection...")
                device.check_connection()
                result = DragonBallLegendsBot(device, config).farm_events()
                self.queue.put(_format_result(result.cycles))
        except ADBError as exc:
            self.queue.put(str(exc))
        except Exception:
            self.queue.put(traceback.format_exc())
        finally:
            self.queue.put("__DONE__")

    def _load_config(self) -> BotConfig:
        config = self._load_config_file()
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

    def _load_config_file(self) -> BotConfig:
        path = Path(self.config_path.get()).expanduser()
        return BotConfig.load(path) if path.exists() else BotConfig()

    def _template_from_fields(self) -> TemplateConfig:
        name = self.template_name.get().strip()
        if not name:
            raise ValueError("Template name is required.")
        path = self.template_path.get().strip()
        if not path:
            raise ValueError("Template path is required.")

        threshold = float(self.template_threshold.get() or "0.88")
        if threshold < 0 or threshold > 1:
            raise ValueError("Template threshold must be between 0 and 1.")

        stride = int(self.template_stride.get() or "4")
        if stride < 1:
            raise ValueError("Template stride must be at least 1.")

        region = self._region_from_fields()
        return TemplateConfig(
            name=name,
            path=path,
            threshold=threshold,
            region=region,
            stride=stride,
        )

    def _region_from_fields(self) -> Region | None:
        values = [
            self.template_region_left.get().strip(),
            self.template_region_top.get().strip(),
            self.template_region_right.get().strip(),
            self.template_region_bottom.get().strip(),
        ]
        if not any(values):
            return None
        if not all(values):
            raise ValueError("Fill all region fields, or leave all of them blank.")

        left, top, right, bottom = [int(value) for value in values]
        if right <= left or bottom <= top:
            raise ValueError("Template region must have right > left and bottom > top.")
        return Region(left, top, right, bottom)

    def _clear_template_fields(self) -> None:
        for variable in (
            self.template_name,
            self.template_path,
            self.template_region_left,
            self.template_region_top,
            self.template_region_right,
            self.template_region_bottom,
        ):
            variable.set("")
        self.template_threshold.set("0.88")
        self.template_stride.set("4")

    def _log_template_summary(self, config: BotConfig) -> None:
        if not config.templates:
            self._log("No templates configured.")
            return
        self._log("Configured templates:")
        for template in config.templates:
            region = "full screen"
            if template.region:
                region = (
                    f"{template.region.left},{template.region.top},"
                    f"{template.region.right},{template.region.bottom}"
                )
            self._log(
                f"- {template.name}: {template.path} "
                f"(threshold={template.threshold}, stride={template.stride}, region={region})"
            )

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
