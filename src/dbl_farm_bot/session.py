"""Session state for the DB Legends farm bot GUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Callable


DEFAULT_EVENTS = [
    "Legends Weekend",
    "Raid Boss",
    "Ultra Space-Time Rush",
    "Bonus Battle",
]


@dataclass
class BotSession:
    """Manage run duration and event rotation independently of the GUI."""

    event_names: list[str] = field(default_factory=lambda: list(DEFAULT_EVENTS))
    clock: Callable[[], float] = field(default=monotonic, repr=False, compare=False)
    is_running: bool = False
    active_event_index: int = 0
    duration_minutes: int = 60
    rotate_events: bool = True
    rotation_interval_minutes: int = 30
    _started_at: float | None = field(default=None, init=False, repr=False)
    _ends_at: float | None = field(default=None, init=False, repr=False)
    _last_rotation_at: float | None = field(default=None, init=False, repr=False)

    @property
    def active_event(self) -> str:
        if not self.event_names:
            return "No events configured"
        return self.event_names[self.active_event_index % len(self.event_names)]

    def start(
        self,
        *,
        duration_minutes: int,
        rotate_events: bool,
        rotation_interval_minutes: int,
        active_event_index: int | None = None,
    ) -> str:
        if duration_minutes < 1:
            raise ValueError("Run duration must be at least 1 minute.")
        if rotation_interval_minutes < 1:
            raise ValueError("Rotation interval must be at least 1 minute.")
        if not self.event_names:
            raise ValueError("Add at least one event before starting.")

        now = self.clock()
        self.duration_minutes = duration_minutes
        self.rotate_events = rotate_events
        self.rotation_interval_minutes = rotation_interval_minutes
        if active_event_index is not None:
            self.active_event_index = active_event_index % len(self.event_names)
        self.is_running = True
        self._started_at = now
        self._ends_at = now + (duration_minutes * 60)
        self._last_rotation_at = now
        return f"Started farming {self.active_event} for {duration_minutes} minutes."

    def stop(self, reason: str = "Stopped") -> str:
        self.is_running = False
        self._started_at = None
        self._ends_at = None
        self._last_rotation_at = None
        return reason

    def rotate_next(self) -> str:
        if not self.event_names:
            return "No events configured"
        self.active_event_index = (self.active_event_index + 1) % len(self.event_names)
        return self.active_event

    def remaining_seconds(self) -> int:
        if not self.is_running or self._ends_at is None:
            return 0
        return max(0, int(round(self._ends_at - self.clock())))

    def tick(self) -> list[str]:
        """Advance timers and return user-facing status messages."""

        if not self.is_running:
            return []

        now = self.clock()
        messages: list[str] = []
        if self._ends_at is not None and now >= self._ends_at:
            messages.append(self.stop("Finished run duration."))
            return messages

        if (
            self.rotate_events
            and self._last_rotation_at is not None
            and now - self._last_rotation_at >= self.rotation_interval_minutes * 60
        ):
            next_event = self.rotate_next()
            self._last_rotation_at = now
            messages.append(f"Rotated to {next_event}.")

        return messages

    def replace_events(self, event_names: list[str]) -> None:
        cleaned = [event.strip() for event in event_names if event.strip()]
        if not cleaned:
            raise ValueError("Keep at least one event in the rotation.")
        self.event_names = cleaned
        self.active_event_index %= len(self.event_names)
