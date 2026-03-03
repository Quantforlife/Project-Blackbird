"""Bridge layer connecting realtime controller and socket server."""
from __future__ import annotations

from app.realtime.controller import RealTimeController


class ControllerBridge:
    """Coordinates controller commands and socket forwarding."""

    def __init__(self, realtime_controller: RealTimeController, socket_bridge) -> None:
        self.controller = realtime_controller
        self.socket_bridge = socket_bridge

    def initialize(self) -> None:
        """Activate socket subscriptions."""
        self.socket_bridge.start()

    def shutdown(self) -> None:
        """Deactivate socket subscriptions and controller loop."""
        self.controller.stop()
        self.socket_bridge.stop()

    def start_live(self) -> dict[str, object]:
        self.controller.start_live()
        return {"mode": "live", "status": "running"}

    def pause(self) -> dict[str, object]:
        self.controller.pause()
        return {"mode": "live", "status": "paused"}

    def resume(self) -> dict[str, object]:
        self.controller.resume()
        return {"mode": "live", "status": "running"}

    def reset(self) -> dict[str, object]:
        self.controller.reset()
        return {"mode": "idle", "status": "reset"}

    def start_playback(self) -> dict[str, object]:
        self.controller.start_playback()
        return {"mode": "playback", "status": "ready"}

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
        self.socket_bridge.socketio.emit("telemetry_update", telemetry)
        self.socket_bridge.socketio.emit(
            "frame_update",
            {
                "frame_id": int(state.get("current_waypoint_index", 0)),
                "drone_pose": state.get("telemetry", {}),
                "detections": state.get("confirmed_detections", []),
            },
        )
        for detection in state.get("confirmed_detections", []):
            self.socket_bridge.socketio.emit(
                "detection_confirmed",
                {
                    "timestamp": state["timestamp"],
                    "detection": detection,
                },
            )
        return state
