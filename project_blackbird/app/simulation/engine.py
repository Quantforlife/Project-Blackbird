"""Deterministic simulation engine controller."""
from __future__ import annotations

import threading
import time

from app.perception.camera import SimulatedCamera
from app.perception.detection_store import DetectionStore
from app.perception.pipeline import PerceptionEngine
from app.realtime.events import (
    BATTERY_UPDATE,
    DETECTION_CONFIRMED,
    EventBus,
    FRAME_CAPTURED,
    MISSION_COMPLETE,
    MISSION_PROGRESS,
    TELEMETRY_UPDATE,
)

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
        perception_model: str = "simulated",
        event_bus: EventBus | None = None,
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
        self.environment.defect_field = self.defect_field

        self.camera = SimulatedCamera(drone=self.drone)
        self.perception_engine = PerceptionEngine(model_type=perception_model)
        self.detection_store = DetectionStore(min_confirmations=2)
        self.event_bus = event_bus or EventBus()

        self._last_frame: dict[str, object] = {}
        self._last_detections: list[dict[str, object]] = []
        self._mission_complete_emitted = False

        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._tick_seconds = 1.0

    def _build_operational_snapshot(self) -> dict[str, object]:
        state = self.drone.get_state()
        return {
            "timestamp": float(state["flight_time_seconds"]),
            "telemetry": {
                "lat": state["latitude"],
                "lon": state["longitude"],
                "altitude": state["altitude"],
                "velocity": state["velocity"],
                "heading": state["heading"],
                "mission_state": state["mission_state"],
            },
            "perception_stats": self.perception_engine.get_stats(),
            "confirmed_detections": self.detection_store.confirmed_detections(),
            "mission_progress": state["mission_progress"],
            "battery": state["battery"],
            "current_waypoint_index": state["current_waypoint_index"],
        }

    def _emit_cycle_events(
        self,
        frame: dict[str, object],
        detections: list[dict[str, object]],
        newly_confirmed: list[dict[str, object]],
    ) -> None:
        snapshot = self._build_operational_snapshot()
        self.event_bus.emit(TELEMETRY_UPDATE, snapshot)
        self.event_bus.emit(
            FRAME_CAPTURED,
            {"timestamp": snapshot["timestamp"], "frame": frame, "detections": detections},
        )

        for detection in newly_confirmed:
            self.event_bus.emit(
                DETECTION_CONFIRMED,
                {
                    "timestamp": snapshot["timestamp"],
                    "detection": detection,
                },
            )

        self.event_bus.emit(
            MISSION_PROGRESS,
            {
                "timestamp": snapshot["timestamp"],
                "mission_progress": snapshot["mission_progress"],
                "current_waypoint_index": snapshot["current_waypoint_index"],
            },
        )
        self.event_bus.emit(
            BATTERY_UPDATE,
            {
                "timestamp": snapshot["timestamp"],
                "battery": snapshot["battery"],
            },
        )

        if (
            snapshot["telemetry"]["mission_state"] == "completed"
            and not self._mission_complete_emitted
        ):
            self._mission_complete_emitted = True
            self.event_bus.emit(MISSION_COMPLETE, snapshot)

    def _process_cycle(self, delta_time: float) -> None:
        self.drone.step(delta_time)
        drone_state = self.drone.get_state()

        frame = self.camera.capture(self.environment, drone_state)
        detections = self.perception_engine.process_frame(frame)
        newly_confirmed = self.detection_store.update(
            detections=detections,
            timestamp=str(drone_state["timestamp"]),
        )

        self._last_frame = frame
        self._last_detections = detections
        self._emit_cycle_events(
            frame=frame,
            detections=detections,
            newly_confirmed=newly_confirmed,
        )

    def _loop(self) -> None:
        while True:
            with self._lock:
                if not self._running:
                    break
                self._process_cycle(self._tick_seconds)
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
        """Reset drone and perception state to initial mission state."""
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
            self.camera = SimulatedCamera(drone=self.drone)
            self.detection_store = DetectionStore(min_confirmations=2)
            self._last_frame = {}
            self._last_detections = []
            self._mission_complete_emitted = False

    def step(self, delta_time: float = 1.0) -> None:
        """Manual deterministic stepping for testability."""
        with self._lock:
            self._process_cycle(delta_time)

    def get_current_state(self) -> dict[str, object]:
        """Return complete deterministic simulation and perception state."""
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
                "last_frame": self._last_frame,
                "last_detections": list(self._last_detections),
                "confirmed_detections": self.detection_store.confirmed_detections(),
                "perception_stats": self.perception_engine.get_stats(),
            }
