"""Mission planner for deterministic grid inspection."""
from __future__ import annotations

from dataclasses import dataclass

from .environment import SolarFarmEnvironment


@dataclass(frozen=True)
class Waypoint:
    """Mission waypoint for drone navigation."""

    latitude: float
    longitude: float
    altitude: float


class GridInspectionMission:
    """Generate serpentine row-by-row inspection waypoints."""

    def __init__(
        self,
        environment: SolarFarmEnvironment,
        inspection_altitude: float = 32.0,
    ) -> None:
        if inspection_altitude <= 0:
            raise ValueError("inspection_altitude must be positive")
        self.environment = environment
        self.inspection_altitude = inspection_altitude

    def generate_waypoints(self) -> list[Waypoint]:
        """Return full farm coverage path in serpentine order."""
        panels_by_row: dict[int, list] = {}
        for panel in self.environment.get_panel_coordinates():
            panels_by_row.setdefault(panel.row, []).append(panel)

        waypoints: list[Waypoint] = []
        for row in range(self.environment.rows):
            row_panels = sorted(panels_by_row[row], key=lambda item: item.col)
            if row % 2 == 1:
                row_panels.reverse()
            for panel in row_panels:
                waypoints.append(
                    Waypoint(
                        latitude=panel.latitude,
                        longitude=panel.longitude,
                        altitude=self.inspection_altitude,
                    )
                )
        return waypoints
