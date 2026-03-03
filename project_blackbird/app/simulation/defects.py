"""Deterministic defect field for solar farm panels."""
from __future__ import annotations

import random
from dataclasses import dataclass

from .environment import METERS_PER_DEG_LAT, SolarFarmEnvironment


@dataclass(frozen=True)
class Defect:
    """Single panel-linked defect."""

    panel_row: int
    panel_col: int
    latitude: float
    longitude: float
    defect_type: str
    severity: str


class DefectField:
    """Deterministically seeded defect assignments for panel grid."""

    def __init__(
        self,
        environment: SolarFarmEnvironment,
        seed: int = 42,
        defect_rate: float = 0.12,
    ) -> None:
        if not 0 <= defect_rate <= 1:
            raise ValueError("defect_rate must be between 0 and 1")
        self.environment = environment
        self.seed = seed
        self.defect_rate = defect_rate
        self._defects = self._generate_defects()

    def _generate_defects(self) -> list[Defect]:
        rng = random.Random(self.seed)
        defect_types = ["hotspot", "crack", "soiling"]
        severity_by_type = {
            "hotspot": "critical",
            "crack": "warning",
            "soiling": "minor",
        }
        output: list[Defect] = []

        for panel in self.environment.get_panel_coordinates():
            if rng.random() <= self.defect_rate:
                d_type = defect_types[rng.randrange(0, len(defect_types))]
                output.append(
                    Defect(
                        panel_row=panel.row,
                        panel_col=panel.col,
                        latitude=panel.latitude,
                        longitude=panel.longitude,
                        defect_type=d_type,
                        severity=severity_by_type[d_type],
                    )
                )
        return output

    def all_defects(self) -> list[Defect]:
        """Return full deterministic defect set."""
        return list(self._defects)

    def get_defects_in_view(
        self,
        latitude: float,
        longitude: float,
        view_radius_meters: float = 8.0,
    ) -> list[Defect]:
        """Return defects near current drone position."""
        if view_radius_meters <= 0:
            return []

        visible: list[Defect] = []
        for defect in self._defects:
            d_lat_m = (latitude - defect.latitude) * METERS_PER_DEG_LAT
            d_lon_m = (longitude - defect.longitude) * METERS_PER_DEG_LAT
            distance = (d_lat_m**2 + d_lon_m**2) ** 0.5
            if distance <= view_radius_meters:
                visible.append(defect)
        return visible
