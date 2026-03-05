"""Thread-safe telemetry simulation engine with playback support."""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime


class TelemetryEngine:
    """Simulates deterministic drone telemetry and defect events."""

    def __init__(self, offline_mode: bool = True) -> None:
        self.offline_mode = offline_mode
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._state = {
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 32.0,
            "speed": 0.0,
            "battery": 100,
            "heading": 90,
            "mission_progress": 0,
            "flight_time": 0,
            "active_defects": 0,
            "images_captured": 0,
            "signal_strength": 98,
            "mode": "live",
            "mission_state": "idle",
        }
        self._logs: deque[dict[str, str]] = deque(maxlen=500)
        self._defect_markers: list[dict[str, float | str | int]] = []
        self._path = self._build_waypoints()
        self._path_index = 0
        self._start_ts = time.time()
        self._paused_elapsed = 0
        self._frame_id = 0
        self._emit_log("INFO", "Mission runtime initialized")

    @staticmethod
    def _build_waypoints() -> list[dict[str, float | int]]:
        base_lat = 37.7749
        base_lon = -122.4194
        points: list[dict[str, float | int]] = []
        heading = 65
        for i in range(120):
            row = i // 20
            col = i % 20
            direction = 1 if row % 2 == 0 else -1
            x = col if direction == 1 else (19 - col)
            lat = base_lat + (row * 0.00028)
            lon = base_lon + (x * 0.00022)
            points.append(
                {
                    "idx": i,
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "alt": 30 + (row % 3),
                    "heading": (heading + (x * 3)) % 360,
                    "speed": 6.0,
                }
            )
        return points

    def _emit_log(self, level: str, message: str) -> None:
        self._logs.append(
            {
                "ts": datetime.utcnow().strftime("%H:%M:%S"),
                "level": level,
                "message": message,
            }
        )

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _run_loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
                if self._state["mission_state"] == "running":
                    self._tick_locked()
            time.sleep(1)

    def _tick_locked(self) -> None:
        if self._path_index >= len(self._path):
            self._state["mission_state"] = "completed"
            self._state["speed"] = 0.0
            self._state["mission_progress"] = 100
            self._emit_log("INFO", "Mission completed")
            return

        point = self._path[self._path_index]
        self._state["latitude"] = point["lat"]
        self._state["longitude"] = point["lon"]
        self._state["altitude"] = point["alt"]
        self._state["heading"] = point["heading"]
        self._state["speed"] = point["speed"]
        self._state["timestamp"] = datetime.utcnow().isoformat()
        self._state["flight_time"] = int(self._paused_elapsed + (time.time() - self._start_ts))
        self._state["mission_progress"] = int((self._path_index / (len(self._path) - 1)) * 100)
        self._state["images_captured"] = self._path_index
        self._state["battery"] = max(18, 100 - int(self._path_index * 0.55))
        self._state["signal_strength"] = max(72, 98 - int(self._path_index * 0.18))

        if self._path_index == 1:
            self._emit_log("GPS", "RTK lock acquired")
        if self._path_index % 8 == 0:
            self._emit_log("SYS", f"Mission sector {self._path_index // 8 + 1} scanning")
        if self._path_index % 12 == 0:
            self._emit_log("NET", "Uplink stable 12ms latency")

        self._frame_id += 1
        if self.offline_mode and self._path_index % 10 == 0:
            severity = "critical" if self._path_index % 20 == 0 else "warning"
            defect = {
                "id": len(self._defect_markers) + 1,
                "lat": self._state["latitude"],
                "lon": self._state["longitude"],
                "type": "thermal_anomaly" if severity == "critical" else "crack",
                "severity": severity,
                "confidence": 91 if severity == "critical" else 78,
                "frame_id": self._frame_id,
                "x": 80 + (self._path_index % 5) * 45,
                "y": 60 + (self._path_index % 4) * 40,
                "w": 90,
                "h": 60,
                "ts": self._state["timestamp"],
            }
            self._defect_markers.append(defect)
            self._state["active_defects"] = len(self._defect_markers)
            self._emit_log(
                "AI",
                f"Thermal anomaly detected at {self._state['latitude']}, {self._state['longitude']}",
            )

        self._path_index += 1

    def command(self, action: str) -> dict[str, str]:
        with self._lock:
            if action == "start" and self._state["mission_state"] in {"idle", "paused"}:
                self._state["mission_state"] = "running"
                self._start_ts = time.time()
                self._emit_log("INFO", "Mission started")
            elif action == "pause" and self._state["mission_state"] == "running":
                self._state["mission_state"] = "paused"
                self._paused_elapsed = self._state["flight_time"]
                self._state["speed"] = 0.0
                self._emit_log("WARN", "Mission paused by operator")
            elif action == "resume" and self._state["mission_state"] == "paused":
                self._state["mission_state"] = "running"
                self._start_ts = time.time()
                self._emit_log("INFO", "Mission resumed")
            elif action == "end":
                self._state["mission_state"] = "completed"
                self._state["speed"] = 0.0
                self._state["mission_progress"] = 100
                self._emit_log("ERROR", "Mission terminated by operator")
            return {"mission_state": self._state["mission_state"]}

    def set_mode(self, mode: str) -> dict[str, str]:
        with self._lock:
            self._state["mode"] = mode if mode in {"live", "playback"} else "live"
            return {"mode": self._state["mode"]}

    def set_playback_index(self, index: int) -> dict[str, int]:
        with self._lock:
            self._path_index = max(0, min(len(self._path) - 1, index))
            point = self._path[self._path_index]
            self._state["latitude"] = point["lat"]
            self._state["longitude"] = point["lon"]
            self._state["altitude"] = point["alt"]
            self._state["heading"] = point["heading"]
            self._state["images_captured"] = self._path_index
            self._state["mission_progress"] = int((self._path_index / (len(self._path) - 1)) * 100)
            return {"index": self._path_index}

    def snapshot(self) -> dict[str, int | float | str]:
        with self._lock:
            return dict(self._state)

    def recent_logs(self, limit: int = 40) -> list[dict[str, str]]:
        with self._lock:
            return list(self._logs)[-limit:]

    def defect_markers(self) -> list[dict[str, float | str | int]]:
        with self._lock:
            return list(self._defect_markers)

    def path_points(self) -> list[dict[str, float | int]]:
        return self._path

    def video_payload(self) -> dict[str, int | str | list[dict[str, int | str]]]:
        with self._lock:
            current_frame = self._frame_id
            boxes = [
                item
                for item in self._defect_markers
                if current_frame - 8 <= int(item["frame_id"]) <= current_frame
            ]
            return {
                "frame_id": current_frame,
                "status": self._state["mission_state"],
                "boxes": [
                    {
                        "x": int(box["x"]),
                        "y": int(box["y"]),
                        "w": int(box["w"]),
                        "h": int(box["h"]),
                        "severity": str(box["severity"]),
                        "type": str(box["type"]),
                        "confidence": int(box["confidence"]),
                    }
                    for box in boxes
                ],
            }
