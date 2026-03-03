"""Thread-safe non-blocking event bus for operational synchronization."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
from collections.abc import Callable

TELEMETRY_UPDATE = "TELEMETRY_UPDATE"
FRAME_CAPTURED = "FRAME_CAPTURED"
DETECTION_CONFIRMED = "DETECTION_CONFIRMED"
MISSION_PROGRESS = "MISSION_PROGRESS"
BATTERY_UPDATE = "BATTERY_UPDATE"
MISSION_COMPLETE = "MISSION_COMPLETE"


class EventBus:
    """In-process publish/subscribe event dispatcher."""

    def __init__(self, max_workers: int = 4) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[Callable[[dict[str, object]], None]]] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def subscribe(self, event_type: str, callback: Callable[[dict[str, object]], None]) -> None:
        """Register callback for an event type."""
        with self._lock:
            callbacks = self._subscribers.setdefault(event_type, [])
            if callback not in callbacks:
                callbacks.append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[dict[str, object]], None]) -> None:
        """Unregister callback from an event type."""
        with self._lock:
            callbacks = self._subscribers.get(event_type, [])
            self._subscribers[event_type] = [cb for cb in callbacks if cb is not callback]

    def emit(self, event_type: str, payload: dict[str, object]) -> None:
        """Emit event to subscribers without blocking caller."""
        with self._lock:
            callbacks = list(self._subscribers.get(event_type, []))
        for callback in callbacks:
            self._executor.submit(callback, payload)

    def shutdown(self) -> None:
        """Shutdown background callback executor."""
        self._executor.shutdown(wait=True)
