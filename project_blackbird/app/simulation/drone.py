"""Deterministic drone physics model."""
from __future__ import annotations

import math
from datetime import datetime

from .environment import METERS_PER_DEG_LAT
from .mission import Waypoint


class SimulatedDrone:
    """Waypoint-following deterministic drone simulation."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        altitude: float,
        velocity_mps: float = 6.0,
    ) -> None:
        if velocity_mps <= 0:
            raise ValueError("velocity_mps must be positive")

        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.velocity_mps = velocity_mps
        self.heading = 0.0
        self.battery = 100.0
        self.mission_state = "idle"
        self.timestamp = datetime.utcnow().isoformat()
        self.current_waypoint_index = 0

        self._mission: list[Waypoint] = []
        self._distance_traveled_m = 0.0
        self._flight_time_seconds = 0.0

    def set_mission(self, waypoints: list[Waypoint]) -> None:
        """Set mission and reset progress to first waypoint."""
        self._mission = list(waypoints)
        self.current_waypoint_index = 0
        if self._mission:
            first = self._mission[0]
            self.latitude = first.latitude
            self.longitude = first.longitude
            self.altitude = first.altitude
            self.mission_state = "running"
        else:
            self.mission_state = "idle"

    def _distance_to(self, target: Waypoint) -> float:
        d_lat_m = (target.latitude - self.latitude) * METERS_PER_DEG_LAT
        d_lon_m = (target.longitude - self.longitude) * METERS_PER_DEG_LAT
        d_alt = target.altitude - self.altitude
        return (d_lat_m**2 + d_lon_m**2 + d_alt**2) ** 0.5

    def step(self, delta_time: float) -> None:
        """Advance simulation by delta_time seconds."""
        if delta_time <= 0:
            return
        if self.mission_state != "running" or not self._mission:
            return

        remaining_time = delta_time
        while remaining_time > 0 and self.mission_state == "running":
            if self.current_waypoint_index >= len(self._mission):
                self.mission_state = "completed"
                self.velocity_mps = 0.0
                break

            target = self._mission[self.current_waypoint_index]
            distance = self._distance_to(target)
            if distance <= 0.01:
                self.current_waypoint_index += 1
                if self.current_waypoint_index >= len(self._mission):
                    self.mission_state = "completed"
                    self.velocity_mps = 0.0
                    break
                continue

            step_distance = min(self.velocity_mps * remaining_time, distance)
            step_time = step_distance / self.velocity_mps
            self.update_position(target, step_distance, distance)
            self.update_battery(step_distance, step_time)

            self._distance_traveled_m += step_distance
            self._flight_time_seconds += step_time
            remaining_time -= step_time

            if step_distance >= distance - 1e-6:
                self.current_waypoint_index += 1
                if self.current_waypoint_index >= len(self._mission):
                    self.mission_state = "completed"
                    self.velocity_mps = 0.0

        self.timestamp = datetime.utcnow().isoformat()

    def update_position(self, target: Waypoint, step_distance: float, full_distance: float) -> None:
        """Linearly interpolate current position towards target waypoint."""
        ratio = 0.0 if full_distance <= 0 else step_distance / full_distance
        new_lat = self.latitude + (target.latitude - self.latitude) * ratio
        new_lon = self.longitude + (target.longitude - self.longitude) * ratio
        new_alt = self.altitude + (target.altitude - self.altitude) * ratio

        d_lat_m = (new_lat - self.latitude) * METERS_PER_DEG_LAT
        d_lon_m = (new_lon - self.longitude) * METERS_PER_DEG_LAT
        self.heading = (math.degrees(math.atan2(d_lon_m, d_lat_m)) + 360.0) % 360.0

        self.latitude = new_lat
        self.longitude = new_lon
        self.altitude = new_alt

    def update_battery(self, step_distance_m: float, step_time_s: float) -> None:
        """Drain battery by distance and airborne time."""
        distance_cost = step_distance_m * 0.002
        time_cost = step_time_s * 0.0035
        self.battery = max(0.0, self.battery - (distance_cost + time_cost))

    def get_state(self) -> dict[str, float | str | int]:
        """Return deterministic state snapshot."""
        progress = 0.0
        if self._mission:
            progress = (self.current_waypoint_index / len(self._mission)) * 100.0

        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "velocity": self.velocity_mps,
            "heading": self.heading,
            "battery": round(self.battery, 2),
            "mission_state": self.mission_state,
            "timestamp": self.timestamp,
            "mission_progress": round(min(progress, 100.0), 2),
            "current_waypoint_index": self.current_waypoint_index,
            "distance_traveled_m": round(self._distance_traveled_m, 2),
            "flight_time_seconds": round(self._flight_time_seconds, 2),
        }
