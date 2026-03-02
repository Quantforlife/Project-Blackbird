"""Thread-safe telemetry simulation engine."""
from __future__ import annotations

import random
import threading
import time
from collections import deque
from datetime import datetime


class TelemetryEngine:
    """Simulates drone telemetry and mission activity in real time."""

    def __init__(self, offline_mode: bool = True) -> None:
        self.offline_mode = offline_mode
        self._rng = random.Random(42)
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._start_ts = time.time()
        self._state = {
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 20.0,
            "speed": 5.5,
            "battery": 100,
            "heading": 90,
            "mission_progress": 0,
            "flight_time": 0,
            "active_defects": 0,
            "images_captured": 0,
        }
        self._logs: deque[str] = deque(maxlen=300)
        self._defect_markers: deque[dict[str, float | str]] = deque(maxlen=100)
        self._emit_log("[INFO] Mission initialized")
        self._emit_log("[GPS] Lock acquired (12 satellites)")

    def _emit_log(self, message: str) -> None:
        self._logs.append(f"{datetime.utcnow().strftime('%H:%M:%S')} {message}")

    def start(self) -> None:
        """Start telemetry loop if not already running."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop telemetry loop."""
        with self._lock:
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _run_loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
                self._tick_locked()
            time.sleep(1)

    def _tick_locked(self) -> None:
        self._state["flight_time"] = int(time.time() - self._start_ts)
        self._state["mission_progress"] = min(100, self._state["mission_progress"] + 1)
        self._state["heading"] = (self._state["heading"] + self._rng.randint(3, 8)) % 360
        self._state["speed"] = round(max(2.0, min(12.0, self._state["speed"] + self._rng.uniform(-0.5, 0.5))), 2)
        self._state["altitude"] = round(max(10.0, min(65.0, self._state["altitude"] + self._rng.uniform(-1.0, 1.0))), 2)
        self._state["battery"] = max(0, self._state["battery"] - (1 if self._state["flight_time"] % 8 == 0 else 0))
        self._state["latitude"] = round(self._state["latitude"] + self._rng.uniform(-0.0004, 0.0004), 6)
        self._state["longitude"] = round(self._state["longitude"] + self._rng.uniform(-0.0004, 0.0004), 6)
        self._state["images_captured"] += 1 if self._state["flight_time"] % 3 == 0 else 0
        self._state["timestamp"] = datetime.utcnow().isoformat()

        if self._state["flight_time"] % 5 == 0:
            self._emit_log(f"[SYS] Uploading frame_{self._state['images_captured']:04d}.jpg")

        if self.offline_mode and self._state["flight_time"] % 7 == 0:
            defect_type = self._rng.choice(["hotspot", "crack", "delamination"])
            marker = {
                "lat": self._state["latitude"],
                "lon": self._state["longitude"],
                "type": defect_type,
            }
            self._defect_markers.append(marker)
            self._state["active_defects"] += 1
            self._emit_log(f"[AI] {defect_type.title()} anomaly detected")

        if self._state["battery"] in {75, 62, 50, 35, 20}:
            self._emit_log(f"[WARN] Battery at {self._state['battery']}%")

    def snapshot(self) -> dict[str, int | float | str]:
        with self._lock:
            return dict(self._state)

    def recent_logs(self, limit: int = 40) -> list[str]:
        with self._lock:
            return list(self._logs)[-limit:]

    def defect_markers(self) -> list[dict[str, float | str]]:
        with self._lock:
            return list(self._defect_markers)
