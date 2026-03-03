"""Socket server bridge for operational real-time events."""
from __future__ import annotations

from collections.abc import Callable
from threading import Lock

from app.realtime.events import (
    BATTERY_UPDATE,
    DETECTION_CONFIRMED,
    FRAME_CAPTURED,
    MISSION_COMPLETE,
    MISSION_PROGRESS,
    TELEMETRY_UPDATE,
)


class SocketServerBridge:
    """Subscribe to EventBus and emit frontend-facing socket events."""

    def __init__(self, event_bus, socketio=None) -> None:
        self.event_bus = event_bus
        self.socketio = socketio or self._create_socketio()
        self._subscriptions: list[tuple[str, Callable[[dict[str, object]], None]]] = []
        self._last_telemetry_signature: tuple[object, ...] | None = None
        self._lock = Lock()

    @staticmethod
    def _create_socketio():
        try:
            from flask_socketio import SocketIO

            return SocketIO(async_mode="threading", cors_allowed_origins="*")
        except Exception:
            class _FallbackSocket:
                def emit(self, *_args, **_kwargs):
                    return None

                def init_app(self, *_args, **_kwargs):
                    return None

            return _FallbackSocket()

    def init_app(self, app) -> None:
        """Initialize socket layer with flask app."""
        if hasattr(self.socketio, "init_app"):
            self.socketio.init_app(app)

    def _telemetry_payload(self, payload: dict[str, object]) -> dict[str, object]:
        telemetry = payload.get("telemetry", {})
        return {
            "timestamp": payload.get("timestamp"),
            "latitude": telemetry.get("lat"),
            "longitude": telemetry.get("lon"),
            "altitude": telemetry.get("altitude"),
            "heading": telemetry.get("heading"),
            "battery": payload.get("battery"),
            "mission_progress": payload.get("mission_progress"),
            "waypoint_index": payload.get("current_waypoint_index"),
        }

    def _on_telemetry(self, payload: dict[str, object]) -> None:
        mapped = self._telemetry_payload(payload)
        signature = (
            mapped.get("latitude"),
            mapped.get("longitude"),
            mapped.get("altitude"),
            mapped.get("heading"),
            mapped.get("battery"),
            mapped.get("mission_progress"),
            mapped.get("waypoint_index"),
        )
        with self._lock:
            if signature == self._last_telemetry_signature:
                return
            self._last_telemetry_signature = signature
        self.socketio.emit("telemetry_update", mapped)

    def _on_frame(self, payload: dict[str, object]) -> None:
        frame = payload.get("frame", {})
        frame_payload = {
            "frame_id": frame.get("frame_id"),
            "drone_pose": frame.get("drone_position", {}),
            "detections": frame.get("defects_visible", []),
        }
        self.socketio.emit("frame_update", frame_payload)

    def _on_detection_confirmed(self, payload: dict[str, object]) -> None:
        detection = payload.get("detection", {})
        self.socketio.emit("detection_confirmed", payload)
        geo = detection.get("geo_location", {})
        self.socketio.emit(
            "terminal_event",
            {
                "timestamp": payload.get("timestamp"),
                "type": "AI",
                "message": (
                    f"{detection.get('defect_type', 'defect')} confirmed at "
                    f"lat {geo.get('latitude')} lon {geo.get('longitude')}"
                ),
            },
        )

    def _on_progress(self, payload: dict[str, object]) -> None:
        self.socketio.emit("mission_progress", payload)

    def _on_battery(self, payload: dict[str, object]) -> None:
        self.socketio.emit("battery_update", payload)

    def _on_complete(self, payload: dict[str, object]) -> None:
        self.socketio.emit("mission_complete", payload)
        self.socketio.emit(
            "terminal_event",
            {
                "timestamp": payload.get("timestamp"),
                "type": "SYSTEM",
                "message": "Mission complete — all waypoints scanned",
            },
        )

    def start(self) -> None:
        """Register all event subscribers."""
        mapping: list[tuple[str, Callable[[dict[str, object]], None]]] = [
            (TELEMETRY_UPDATE, self._on_telemetry),
            (FRAME_CAPTURED, self._on_frame),
            (DETECTION_CONFIRMED, self._on_detection_confirmed),
            (MISSION_PROGRESS, self._on_progress),
            (BATTERY_UPDATE, self._on_battery),
            (MISSION_COMPLETE, self._on_complete),
        ]
        for event_type, callback in mapping:
            self.event_bus.subscribe(event_type, callback)
            self._subscriptions.append((event_type, callback))

    def stop(self) -> None:
        """Unsubscribe all handlers."""
        for event_type, callback in self._subscriptions:
            self.event_bus.unsubscribe(event_type, callback)
        self._subscriptions.clear()
