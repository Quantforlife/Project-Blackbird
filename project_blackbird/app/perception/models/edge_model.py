"""Pluggable edge defect model wrapper."""
from __future__ import annotations

import math


class EdgeDefectModel:
    """Model abstraction supporting simulated and optional edge backends."""

    def __init__(self, backend: str = "simulated") -> None:
        self.backend = backend
        self.loaded = False
        self._runtime = "simulated"

    def load(self) -> str:
        """Load backend runtime with graceful fallback."""
        selected = self.backend.lower()
        if selected == "simulated":
            self.loaded = True
            self._runtime = "simulated"
            return self._runtime

        if selected in {"tiny", "onnx"}:
            try:
                import onnxruntime  # type: ignore # noqa: F401

                self._runtime = "onnx"
                self.loaded = True
                return self._runtime
            except Exception:
                self._runtime = "simulated"
                self.loaded = True
                return self._runtime

        if selected == "tensorrt":
            try:
                import tensorrt  # type: ignore # noqa: F401

                self._runtime = "tensorrt"
                self.loaded = True
                return self._runtime
            except Exception:
                self._runtime = "simulated"
                self.loaded = True
                return self._runtime

        self._runtime = "simulated"
        self.loaded = True
        return self._runtime

    def infer(self, frame_data: dict[str, object]) -> list[dict[str, object]]:
        """Infer defects from frame metadata."""
        if not self.loaded:
            self.load()

        if self._runtime in {"onnx", "tensorrt"}:
            # Runtime adapter placeholder; deterministic fallback retained for offline operation.
            return self._infer_simulated(frame_data)
        return self._infer_simulated(frame_data)

    def _infer_simulated(self, frame_data: dict[str, object]) -> list[dict[str, object]]:
        visible_panels = {
            panel["panel_id"]: panel for panel in frame_data.get("visible_panels", [])
        }
        defects = frame_data.get("defects_visible", [])
        drone_pos = frame_data.get("drone_position", {})
        camera_info = frame_data.get("camera", {})
        altitude = float(drone_pos.get("altitude", 30.0))
        footprint = float(camera_info.get("ground_footprint_m", 30.0))
        center_x = float(camera_info.get("resolution", (640, 384))[0]) / 2.0
        center_y = float(camera_info.get("resolution", (640, 384))[1]) / 2.0
        angle = float(camera_info.get("mounting_angle_degrees", 90.0))

        detections: list[dict[str, object]] = []
        for defect in defects:
            panel_id = defect["panel_id"]
            panel = visible_panels.get(panel_id)
            if panel is None:
                continue

            px, py = panel["pixel_center"]
            dist_center_px = ((px - center_x) ** 2 + (py - center_y) ** 2) ** 0.5
            max_center = ((center_x**2 + center_y**2) ** 0.5) + 1e-9
            center_factor = max(0.2, 1.0 - (dist_center_px / max_center))
            altitude_factor = max(0.25, 1.0 - ((altitude - 20.0) / 120.0))
            angle_factor = max(0.35, math.cos(math.radians(abs(angle - 90.0))))

            confidence = min(0.99, max(0.05, 0.95 * center_factor * altitude_factor * angle_factor))
            box_w = max(24, int(130.0 / max(1.0, altitude / 8.0)))
            box_h = max(18, int(90.0 / max(1.0, altitude / 8.0)))
            bbox = {
                "x": int(px - box_w / 2),
                "y": int(py - box_h / 2),
                "w": box_w,
                "h": box_h,
            }

            detections.append(
                {
                    "panel_id": panel_id,
                    "defect_type": defect["defect_type"],
                    "confidence": round(confidence, 4),
                    "bounding_box": bbox,
                    "geo_location": {
                        "latitude": defect["latitude"],
                        "longitude": defect["longitude"],
                    },
                    "severity": defect.get("severity", "minor"),
                    "distance_from_center_m": round(
                        ((panel["distance_north_m"] ** 2 + panel["distance_east_m"] ** 2) ** 0.5), 4
                    ),
                    "altitude_m": altitude,
                    "view_footprint_m": footprint,
                }
            )

        return detections
