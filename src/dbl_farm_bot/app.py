"""Tkinter desktop GUI for the DB Legends farm bot."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .session import BotSession


class BotGui:
    """Clean control panel for running and rotating farm events."""

    def __init__(self, root: tk.Tk, session: BotSession | None = None) -> None:
        self.root = root
        self.session = session or BotSession()
        self.duration_var = tk.StringVar(value="60")
        self.rotation_interval_var = tk.StringVar(value="30")
        self.rotate_var = tk.BooleanVar(value=True)
        self.new_event_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.active_event_var = tk.StringVar(value=self.session.active_event)
        self.remaining_var = tk.StringVar(value="Not running")
        self._build_window()
        self._refresh_event_list()
        self._schedule_tick()

    def _build_window(self) -> None:
        self.root.title("DB Legends Farm Bot")
        self.root.geometry("900x560")
        self.root.minsize(780, 500)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("Panel.TFrame", background="#111827")
        style.configure("Card.TFrame", background="#1f2937")
        style.configure("TLabel", background="#111827", foreground="#e5e7eb", font=("Segoe UI", 10))
        style.configure("Title.TLabel", background="#111827", foreground="#f8fafc", font=("Segoe UI", 22, "bold"))
        style.configure("Muted.TLabel", background="#111827", foreground="#94a3b8", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#1f2937", foreground="#f8fafc", font=("Segoe UI", 13, "bold"))
        style.configure("Hero.TLabel", background="#111827", foreground="#38bdf8", font=("Segoe UI", 12, "bold"))
        style.configure("TCheckbutton", background="#1f2937", foreground="#e5e7eb", font=("Segoe UI", 10))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=(18, 10))
        style.configure("Danger.TButton", font=("Segoe UI", 11, "bold"), padding=(18, 10))
        style.map("Primary.TButton", background=[("active", "#0284c7"), ("!disabled", "#0ea5e9")])
        style.map("Danger.TButton", background=[("active", "#b91c1c"), ("!disabled", "#ef4444")])

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        sidebar = ttk.Frame(outer, style="Panel.TFrame", padding=24)
        sidebar.pack(side="left", fill="y")

        ttk.Label(sidebar, text="DB Legends", style="Title.TLabel").pack(anchor="w")
        ttk.Label(sidebar, text="Farm Bot Control", style="Muted.TLabel").pack(anchor="w", pady=(2, 24))
        ttk.Label(sidebar, textvariable=self.status_var, style="Hero.TLabel").pack(anchor="w", pady=(0, 18))

        self.start_button = ttk.Button(sidebar, text="Start", style="Primary.TButton", command=self._start)
        self.start_button.pack(fill="x", pady=(0, 10))
        self.stop_button = ttk.Button(sidebar, text="Stop", style="Danger.TButton", command=self._stop, state="disabled")
        self.stop_button.pack(fill="x", pady=(0, 10))
        ttk.Button(sidebar, text="Rotate Event Now", command=self._rotate_now).pack(fill="x")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=24)
        ttk.Label(sidebar, text="Active event", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(sidebar, textvariable=self.active_event_var, style="Hero.TLabel", wraplength=210).pack(
            anchor="w",
            pady=(4, 16),
        )
        ttk.Label(sidebar, text="Remaining", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(sidebar, textvariable=self.remaining_var, style="Hero.TLabel").pack(anchor="w", pady=(4, 0))

        main = ttk.Frame(outer, style="Panel.TFrame", padding=(20, 0, 0, 0))
        main.pack(side="left", fill="both", expand=True)

        header = ttk.Frame(main, style="Panel.TFrame")
        header.pack(fill="x", pady=(0, 16))
        ttk.Label(header, text="Bot Menu", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Choose a run length, select events, and rotate through rewards automatically.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        cards = ttk.Frame(main, style="Panel.TFrame")
        cards.pack(fill="both", expand=True)
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)
        cards.rowconfigure(1, weight=1)

        run_card = self._card(cards, "Run settings")
        run_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        self._choice_field(
            run_card,
            "How long to run (minutes)",
            self.duration_var,
            ("1", "5", "15", "30", "60", "120", "240", "480", "720"),
        )
        ttk.Checkbutton(run_card, text="Rotate events while running", variable=self.rotate_var).pack(
            anchor="w",
            pady=(16, 8),
        )
        self._choice_field(
            run_card,
            "Rotate every (minutes)",
            self.rotation_interval_var,
            ("1", "5", "10", "15", "30", "60", "120", "240"),
        )

        event_card = self._card(cards, "Event rotation")
        event_card.grid(row=0, column=1, rowspan=2, sticky="nsew", pady=(0, 12))
        event_card.rowconfigure(1, weight=1)
        ttk.Label(event_card, text="Events are farmed from top to bottom.", style="Muted.TLabel").pack(
            anchor="w",
            pady=(0, 8),
        )
        self.event_list = tk.Listbox(
            event_card,
            activestyle="dotbox",
            background="#0b1220",
            borderwidth=0,
            foreground="#e5e7eb",
            highlightthickness=1,
            highlightbackground="#334155",
            selectbackground="#0ea5e9",
            selectforeground="#ffffff",
            font=("Segoe UI", 11),
        )
        self.event_list.pack(fill="both", expand=True)
        self.event_list.bind("<<ListboxSelect>>", lambda _event: self._sync_active_from_selection())

        event_entry = ttk.Frame(event_card, style="Card.TFrame")
        event_entry.pack(fill="x", pady=(12, 0))
        ttk.Entry(event_entry, textvariable=self.new_event_var).pack(side="left", fill="x", expand=True)
        ttk.Button(event_entry, text="Add", command=self._add_event).pack(side="left", padx=(8, 0))
        ttk.Button(event_entry, text="Remove", command=self._remove_event).pack(side="left", padx=(8, 0))

        log_card = self._card(cards, "Activity")
        log_card.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.log = tk.Text(
            log_card,
            height=9,
            background="#0b1220",
            borderwidth=0,
            foreground="#cbd5e1",
            insertbackground="#e5e7eb",
            relief="flat",
            wrap="word",
        )
        self.log.pack(fill="both", expand=True)
        self._log("Ready. Configure your run and press Start.")

    def _card(self, parent: ttk.Frame, title: str) -> ttk.Frame:
        card = ttk.Frame(parent, style="Card.TFrame", padding=18)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w", pady=(0, 14))
        return card

    def _choice_field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
    ) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor="w")
        ttk.Combobox(parent, state="readonly", textvariable=variable, values=values, width=12).pack(
            anchor="w",
            pady=(4, 0),
        )

    def _start(self) -> None:
        try:
            message = self.session.start(
                duration_minutes=int(self.duration_var.get()),
                rotate_events=bool(self.rotate_var.get()),
                rotation_interval_minutes=int(self.rotation_interval_var.get()),
                active_event_index=self._selected_index(),
            )
        except (tk.TclError, ValueError) as error:
            messagebox.showerror("Cannot start bot", str(error))
            return
        self.status_var.set("Running")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self._sync_display()
        self._log(message)

    def _stop(self) -> None:
        self._log(self.session.stop())
        self.status_var.set("Ready")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self._sync_display()

    def _rotate_now(self) -> None:
        next_event = self.session.rotate_next()
        self._select_active_event()
        self._sync_display()
        self._log(f"Rotated to {next_event}.")

    def _add_event(self) -> None:
        event_name = self.new_event_var.get().strip()
        if not event_name:
            return
        self.session.replace_events([*self.session.event_names, event_name])
        self.new_event_var.set("")
        self._refresh_event_list()
        self._log(f"Added event: {event_name}.")

    def _remove_event(self) -> None:
        index = self._selected_index()
        remaining = [event for item, event in enumerate(self.session.event_names) if item != index]
        try:
            self.session.replace_events(remaining)
        except ValueError as error:
            messagebox.showerror("Cannot remove event", str(error))
            return
        self._refresh_event_list()
        self._sync_display()
        self._log("Removed selected event.")

    def _sync_active_from_selection(self) -> None:
        self.session.active_event_index = self._selected_index()
        self._sync_display()

    def _selected_index(self) -> int:
        selection = self.event_list.curselection() if hasattr(self, "event_list") else ()
        return selection[0] if selection else self.session.active_event_index

    def _refresh_event_list(self) -> None:
        self.event_list.delete(0, tk.END)
        for event_name in self.session.event_names:
            self.event_list.insert(tk.END, event_name)
        self._select_active_event()

    def _select_active_event(self) -> None:
        if not self.session.event_names:
            return
        self.event_list.selection_clear(0, tk.END)
        index = self.session.active_event_index % len(self.session.event_names)
        self.event_list.selection_set(index)
        self.event_list.activate(index)
        self.event_list.see(index)

    def _sync_display(self) -> None:
        self.active_event_var.set(self.session.active_event)
        remaining = self.session.remaining_seconds()
        self.remaining_var.set(self._format_remaining(remaining) if self.session.is_running else "Not running")

    def _schedule_tick(self) -> None:
        for message in self.session.tick():
            self._log(message)
            if not self.session.is_running:
                self.status_var.set("Ready")
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
        self._select_active_event()
        self._sync_display()
        self.root.after(1000, self._schedule_tick)

    def _format_remaining(self, seconds: int) -> str:
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        return f"{minutes}m {seconds:02d}s"

    def _log(self, message: str) -> None:
        self.log.insert(tk.END, f"{message}\n")
        self.log.see(tk.END)


def main() -> None:
    root = tk.Tk()
    BotGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
