"""Deterministic simulated camera model."""
from __future__ import annotations

import math

from app.simulation.environment import METERS_PER_DEG_LAT, SolarFarmEnvironment


class SimulatedCamera:
    """Camera model attached to simulated drone."""

    def __init__(
        self,
        drone,
        fov_degrees: float = 62.0,
        resolution: tuple[int, int] = (640, 384),
        mounting_angle_degrees: float = 90.0,
    ) -> None:
        if fov_degrees <= 0 or fov_degrees >= 180:
            raise ValueError("fov_degrees must be in (0, 180)")
        if resolution[0] <= 0 or resolution[1] <= 0:
            raise ValueError("resolution values must be positive")

        self.drone = drone
        self.fov_degrees = fov_degrees
        self.resolution = resolution
        self.mounting_angle_degrees = mounting_angle_degrees
        self._frame_id = 0

    def _lon_meters_per_degree(self, latitude: float) -> float:
        return METERS_PER_DEG_LAT * max(0.01, abs(math.cos(math.radians(latitude))))

    def _ground_footprint(self, altitude: float) -> float:
        effective_fov = self.fov_degrees * max(
            0.25,
            abs(math.cos(math.radians(self.mounting_angle_degrees - 90.0))),
        )
        effective_fov = max(8.0, effective_fov)
        return 2.0 * altitude * math.tan(math.radians(effective_fov / 2.0))

    def capture(
        self,
        environment: SolarFarmEnvironment,
        drone_state: dict[str, float | int | str],
    ) -> dict[str, object]:
        """Capture deterministic frame metadata from drone viewpoint."""
        self._frame_id += 1
        latitude = float(drone_state["latitude"])
        longitude = float(drone_state["longitude"])
        altitude = float(drone_state["altitude"])

        footprint = self._ground_footprint(altitude)
        half_span = footprint / 2.0
        lon_meter = self._lon_meters_per_degree(latitude)

        visible_panels: list[dict[str, object]] = []
        for panel in environment.get_panel_coordinates():
            d_north_m = (panel.latitude - latitude) * METERS_PER_DEG_LAT
            d_east_m = (panel.longitude - longitude) * lon_meter
            if abs(d_north_m) <= half_span and abs(d_east_m) <= half_span:
                x_norm = 0.5 + (d_east_m / footprint)
                y_norm = 0.5 - (d_north_m / footprint)
                x_px = int(max(0, min(self.resolution[0] - 1, x_norm * self.resolution[0])))
                y_px = int(max(0, min(self.resolution[1] - 1, y_norm * self.resolution[1])))
                panel_id = f"r{panel.row}c{panel.col}"
                visible_panels.append(
                    {
                        "panel_id": panel_id,
                        "row": panel.row,
                        "col": panel.col,
                        "latitude": panel.latitude,
                        "longitude": panel.longitude,
                        "distance_north_m": d_north_m,
                        "distance_east_m": d_east_m,
                        "pixel_center": (x_px, y_px),
                    }
                )

        defects_visible: list[dict[str, object]] = []
        defects = []
        if hasattr(environment, "defect_field") and environment.defect_field is not None:
            defects = environment.defect_field.all_defects()

        visible_ids = {item["panel_id"] for item in visible_panels}
        for defect in defects:
            panel_id = f"r{defect.panel_row}c{defect.panel_col}"
            if panel_id in visible_ids:
                defects_visible.append(
                    {
                        "panel_id": panel_id,
                        "defect_type": defect.defect_type,
                        "severity": defect.severity,
                        "latitude": defect.latitude,
                        "longitude": defect.longitude,
                    }
                )

        return {
            "frame_id": self._frame_id,
            "drone_position": {
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "heading": float(drone_state.get("heading", 0.0)),
            },
            "camera": {
                "fov_degrees": self.fov_degrees,
                "resolution": self.resolution,
                "mounting_angle_degrees": self.mounting_angle_degrees,
                "ground_footprint_m": footprint,
            },
            "visible_panels": visible_panels,
            "defects_visible": defects_visible,
        }
