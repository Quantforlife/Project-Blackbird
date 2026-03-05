"""Solar farm environment model."""
from __future__ import annotations

import math
from dataclasses import dataclass


METERS_PER_DEG_LAT = 111_320.0


@dataclass(frozen=True)
class PanelCoordinate:
    """Single panel center coordinate and grid index."""

    row: int
    col: int
    latitude: float
    longitude: float


class SolarFarmEnvironment:
    """Deterministic solar farm grid mapped to lat/lon coordinates."""

    def __init__(
        self,
        origin_latitude: float,
        origin_longitude: float,
        rows: int,
        columns: int,
        panel_spacing_meters: float,
    ) -> None:
        if rows <= 0 or columns <= 0:
            raise ValueError("rows and columns must be positive")
        if panel_spacing_meters <= 0:
            raise ValueError("panel_spacing_meters must be positive")

        self.origin_latitude = origin_latitude
        self.origin_longitude = origin_longitude
        self.rows = rows
        self.columns = columns
        self.panel_spacing_meters = panel_spacing_meters

        self.total_width_meters = (columns - 1) * panel_spacing_meters
        self.total_height_meters = (rows - 1) * panel_spacing_meters

        self._panels = self._build_grid()

    def _meters_to_lat_offset(self, meters: float) -> float:
        return meters / METERS_PER_DEG_LAT

    def _meters_to_lon_offset(self, meters: float, at_latitude: float) -> float:
        meters_per_deg_lon = METERS_PER_DEG_LAT * max(
            0.01, abs(math.cos(math.radians(at_latitude)))
        )
        return meters / meters_per_deg_lon

    def _build_grid(self) -> list[PanelCoordinate]:
        grid: list[PanelCoordinate] = []
        for row in range(self.rows):
            north_m = row * self.panel_spacing_meters
            lat = self.origin_latitude + self._meters_to_lat_offset(north_m)
            for col in range(self.columns):
                east_m = col * self.panel_spacing_meters
                lon = self.origin_longitude + self._meters_to_lon_offset(east_m, lat)
                grid.append(PanelCoordinate(row=row, col=col, latitude=lat, longitude=lon))
        return grid

    def get_panel_coordinates(self) -> list[PanelCoordinate]:
        """Return all panel center coordinates in row-major order."""
        return list(self._panels)

    def get_farm_bounds(self) -> dict[str, float]:
        """Return bounding box coordinates for the farm."""
        lats = [panel.latitude for panel in self._panels]
        lons = [panel.longitude for panel in self._panels]
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
            "width_meters": self.total_width_meters,
            "height_meters": self.total_height_meters,
        }

    def get_panel_at_position(self, latitude: float, longitude: float) -> PanelCoordinate | None:
        """Return nearest panel center if position is within half spacing threshold."""
        threshold = self.panel_spacing_meters * 0.5
        nearest: PanelCoordinate | None = None
        nearest_distance = float("inf")

        for panel in self._panels:
            d_lat_m = (latitude - panel.latitude) * METERS_PER_DEG_LAT
            d_lon_m = (longitude - panel.longitude) * METERS_PER_DEG_LAT
            distance = (d_lat_m**2 + d_lon_m**2) ** 0.5
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = panel

        if nearest is None:
            return None
        if nearest_distance <= threshold:
            return nearest
        return None
