"""Bridge layer connecting realtime controller and socket server."""
from __future__ import annotations

import logging
from threading import Lock

from app.realtime.controller import RealTimeController


class ControllerBridge:
    """Coordinates controller commands and socket forwarding."""

    _instances = 0

    def __init__(self, realtime_controller: RealTimeController, socket_bridge, diagnostics_enabled: bool = False) -> None:
        self.controller = realtime_controller
        self.socket_bridge = socket_bridge
        self._initialized = False
        self._lock = Lock()
        self.diagnostics_enabled = diagnostics_enabled
        self.log = logging.getLogger("blackbird.controller_bridge")
        ControllerBridge._instances += 1

    def _dbg(self, message: str, **data: object) -> None:
        if self.diagnostics_enabled:
            self.log.warning("[controller_bridge] %s | %s", message, data)

    def initialize(self) -> None:
        with self._lock:
            if self._initialized:
                return
            self.socket_bridge.start()
            self._initialized = True
            self._dbg("initialize")

    def shutdown(self) -> None:
        with self._lock:
            if not self._initialized:
                return
            self.controller.stop()
            self.socket_bridge.stop()
            self._initialized = False
            self._dbg("shutdown")

    def start_live(self) -> dict[str, object]:
        started, reason = self.controller.start_live()
        status = "running" if started else "blocked"
        payload = {
            "mode": "live",
            "status": status,
            "reason": reason,
            "controller": self.controller.status(),
        }
        self._dbg("start_live", payload=payload)
        return payload

    def pause(self) -> dict[str, object]:
        self.controller.pause()
        return {"mode": "live", "status": "paused", "controller": self.controller.status()}

    def resume(self) -> dict[str, object]:
        self.controller.resume()
        return {"mode": "live", "status": "running", "controller": self.controller.status()}

    def reset(self) -> dict[str, object]:
        self.controller.reset()
        return {"mode": "idle", "status": "reset", "controller": self.controller.status()}

    def end(self) -> dict[str, object]:
        self.controller.end()
        return {"mode": "idle", "status": "ended", "controller": self.controller.status()}

    def start_playback(self) -> dict[str, object]:
        self.controller.start_playback()
        return {"mode": "playback", "status": "ready", "controller": self.controller.status()}

    def diagnostics(self) -> dict[str, object]:
        return {
            "controller": self.controller.status(),
            "bridge_initialized": self._initialized,
            "controller_bridge_instances": ControllerBridge._instances,
            "socket_subscriptions": self.socket_bridge.subscription_count,
            "socket_events": self.socket_bridge.event_counts,
        }

    def seek(self, timestamp: float) -> dict[str, object] | None:
        state = self.controller.seek(timestamp)
        if state is None:
            return None

        telemetry = {
            "timestamp": state["timestamp"],
            "latitude": state["telemetry"].get("lat"),
            "longitude": state["telemetry"].get("lon"),
            "altitude": state["telemetry"].get("altitude"),
            "heading": state["telemetry"].get("heading"),
            "battery": state.get("battery"),
            "mission_progress": state.get("mission_progress"),
            "waypoint_index": state.get("current_waypoint_index"),
        }
        for event_name, payload in (
            ("telemetry_update", telemetry),
            (
                "frame_update",
                {
                    "frame_id": int(state.get("current_waypoint_index", 0)),
                    "drone_pose": state.get("telemetry", {}),
                    "detections": state.get("confirmed_detections", []),
                },
            ),
        ):
            try:
                self.socket_bridge.socketio.emit(event_name, payload)
            except Exception:
                continue

        for detection in state.get("confirmed_detections", []):
            try:
                self.socket_bridge.socketio.emit(
                    "detection_confirmed",
                    {
                        "timestamp": state["timestamp"],
                        "detection": detection,
                    },
                )
            except Exception:
                continue
        return state
