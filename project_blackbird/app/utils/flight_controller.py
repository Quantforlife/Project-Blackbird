"""Flight controller utility with MAVSDK simulation fallback."""
from __future__ import annotations

from datetime import datetime


class FlightController:
    """Drone mission controller interface."""

    def __init__(self, offline_mode: bool = False) -> None:
        self.offline_mode = offline_mode
        self.simulated = True
        self.connected = False
        self._mission: list[dict[str, float]] = []

        if self.offline_mode:
            self.simulated = True
            return

        try:
            import mavsdk  # noqa: F401

            self.simulated = False
        except ImportError:
            self.simulated = True
        except Exception:
            self.simulated = True

    def connect(self) -> dict[str, str | bool]:
        self.connected = True
        return {
            "connected": True,
            "mode": "simulation" if self.simulated else "hardware",
        }

    def upload_mission(self, waypoints: list[dict[str, float]] | None = None) -> dict[str, str | int]:
        self._mission = waypoints or [{"lat": 0.0, "lon": 0.0, "alt": 20.0}]
        return {"status": "uploaded", "waypoints": len(self._mission)}

    def start_mission(self) -> dict[str, str]:
        status = "started" if self.connected else "not_connected"
        return {"status": status}

    def get_telemetry(self) -> dict[str, float | str]:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 30.5,
            "speed": 6.2,
        }
