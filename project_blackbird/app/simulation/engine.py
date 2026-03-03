"""Deterministic simulation engine controller."""
from __future__ import annotations

import threading
import time

from .defects import DefectField
from .drone import SimulatedDrone
from .environment import SolarFarmEnvironment
from .mission import GridInspectionMission


class SimulationEngine:
    """Owns environment, mission, drone, and deterministic update lifecycle."""

    def __init__(
        self,
        origin_latitude: float = 37.7749,
        origin_longitude: float = -122.4194,
        rows: int = 8,
        columns: int = 12,
        panel_spacing_meters: float = 6.0,
        inspection_altitude: float = 32.0,
        velocity_mps: float = 6.0,
    ) -> None:
        self.environment = SolarFarmEnvironment(
            origin_latitude=origin_latitude,
            origin_longitude=origin_longitude,
            rows=rows,
            columns=columns,
            panel_spacing_meters=panel_spacing_meters,
        )
        self.mission = GridInspectionMission(
            environment=self.environment,
            inspection_altitude=inspection_altitude,
        )
        self.waypoints = self.mission.generate_waypoints()
        first = self.waypoints[0]
        self.drone = SimulatedDrone(
            latitude=first.latitude,
            longitude=first.longitude,
            altitude=first.altitude,
            velocity_mps=velocity_mps,
        )
        self.drone.set_mission(self.waypoints)
        self.defect_field = DefectField(self.environment)

        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._tick_seconds = 1.0

    def _loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
                self.drone.step(self._tick_seconds)
            time.sleep(self._tick_seconds)

    def start(self) -> None:
        """Start 1Hz simulation loop."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def pause(self) -> None:
        """Pause simulation loop."""
        with self._lock:
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def reset(self) -> None:
        """Reset drone to initial mission state."""
        self.pause()
        with self._lock:
            first = self.waypoints[0]
            self.drone = SimulatedDrone(
                latitude=first.latitude,
                longitude=first.longitude,
                altitude=first.altitude,
                velocity_mps=6.0,
            )
            self.drone.set_mission(self.waypoints)

    def step(self, delta_time: float = 1.0) -> None:
        """Manual deterministic stepping for testability."""
        with self._lock:
            self.drone.step(delta_time)

    def get_current_state(self) -> dict[str, float | int | str | list[dict[str, object]]]:
        """Return complete deterministic simulation state."""
        with self._lock:
            drone_state = self.drone.get_state()
            visible_defects = self.defect_field.get_defects_in_view(
                latitude=float(drone_state["latitude"]),
                longitude=float(drone_state["longitude"]),
            )
            return {
                "lat": drone_state["latitude"],
                "lon": drone_state["longitude"],
                "altitude": drone_state["altitude"],
                "battery": drone_state["battery"],
                "mission_progress": drone_state["mission_progress"],
                "current_waypoint_index": drone_state["current_waypoint_index"],
                "mission_state": drone_state["mission_state"],
                "visible_defects": [
                    {
                        "row": d.panel_row,
                        "col": d.panel_col,
                        "type": d.defect_type,
                        "severity": d.severity,
                    }
                    for d in visible_defects
                ],
            }
