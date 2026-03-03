"""AI inference utility with graceful fallback."""
from __future__ import annotations

from typing import Any


class AIInference:
    """Performs defect inference with optional backend."""

    def __init__(self, model_path: str | None = None, offline_mode: bool = False) -> None:
        self.model = None
        self.offline_mode = offline_mode
        if self.offline_mode:
            return

        try:
            import torch  # noqa: F401
            from ultralytics import YOLO  # type: ignore

            if model_path:
                self.model = YOLO(model_path)
        except ImportError:
            self.model = None
        except Exception:
            self.model = None

    def infer(self, frame: Any) -> list[dict[str, float | str]]:
        """Run inference or return deterministic dummy detections."""
        fallback_detections = [
            {
                "defect_type": "hotspot",
                "confidence": 0.91,
                "x": 120.0,
                "y": 80.0,
            },
            {
                "defect_type": "crack",
                "confidence": 0.84,
                "x": 240.0,
                "y": 145.0,
            },
        ]

        if self.model is None:
            return fallback_detections

        try:
            results = self.model.predict(frame)
        except Exception:
            self.model = None
            return fallback_detections

        parsed: list[dict[str, float | str]] = []
        for result in results:
            for box in result.boxes:
                parsed.append(
                    {
                        "defect_type": str(result.names[int(box.cls)]),
                        "confidence": float(box.conf),
                        "x": float(box.xyxy[0][0]),
                        "y": float(box.xyxy[0][1]),
                    }
                )
        return parsed
