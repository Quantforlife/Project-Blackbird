"""Mission timeline recorder for deterministic playback."""
from __future__ import annotations

import bisect
from copy import deepcopy


class MissionTimeline:
    """Stores ordered operational state snapshots with retention controls."""

    def __init__(self, max_history_length: int = 10_000) -> None:
        if max_history_length <= 0:
            raise ValueError("max_history_length must be positive")
        self.max_history_length = max_history_length
        self._snapshots: list[dict[str, object]] = []
        self._timestamps: list[float] = []

    def add(self, snapshot: dict[str, object]) -> None:
        """Append snapshot in timestamp order."""
        item = deepcopy(snapshot)
        timestamp = float(item["timestamp"])
        self._snapshots.append(item)
        self._timestamps.append(timestamp)

        overflow = len(self._snapshots) - self.max_history_length
        if overflow > 0:
            self._snapshots = self._snapshots[overflow:]
            self._timestamps = self._timestamps[overflow:]

    def get_state_at(self, timestamp: float) -> dict[str, object] | None:
        """Return exact or nearest previous snapshot at timestamp."""
        if not self._timestamps:
            return None
        idx = bisect.bisect_right(self._timestamps, timestamp) - 1
        if idx < 0:
            return deepcopy(self._snapshots[0])
        return deepcopy(self._snapshots[idx])

    def get_all(self) -> list[dict[str, object]]:
        """Return full ordered snapshot list."""
        return deepcopy(self._snapshots)

    def duration(self) -> float:
        """Return timeline duration seconds."""
        if len(self._timestamps) < 2:
            return 0.0
        return self._timestamps[-1] - self._timestamps[0]
