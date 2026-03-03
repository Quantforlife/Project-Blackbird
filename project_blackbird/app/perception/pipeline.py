"""Perception processing pipeline."""
from __future__ import annotations

import time

from app.performance.constraints import MAX_INFERENCE_TIME_MS, TARGET_EDGE_FPS
from app.perception.models.edge_model import EdgeDefectModel


class PerceptionEngine:
    """Run model inference on frame payloads with edge constraints."""

    def __init__(self, model_type: str = "simulated") -> None:
        self.model_type = model_type
        self.model = EdgeDefectModel(backend=model_type)
        self.runtime = self.model.load()

        self._last_inference_ts = 0.0
        self._inference_count = 0
        self._avg_inference_ms = 0.0
        self._last_inference_ms = 0.0
        self._dropped_frames = 0

    def _simulate_inference_latency_ms(self, frame_data: dict[str, object]) -> float:
        panel_count = len(frame_data.get("visible_panels", []))
        base_ms = 12.0
        per_panel_ms = 1.6
        simulated = base_ms + (panel_count * per_panel_ms)
        return min(float(MAX_INFERENCE_TIME_MS), simulated)

    def process_frame(self, frame_data: dict[str, object]) -> list[dict[str, object]]:
        """Process one frame and return detections under edge FPS constraints."""
        now = time.perf_counter()
        min_dt = 1.0 / max(1, TARGET_EDGE_FPS)
        if now - self._last_inference_ts < min_dt:
            self._dropped_frames += 1
            return []

        simulated_ms = self._simulate_inference_latency_ms(frame_data)
        detections = self.model.infer(frame_data)

        self._last_inference_ts = now
        self._last_inference_ms = simulated_ms
        self._inference_count += 1
        self._avg_inference_ms = (
            ((self._avg_inference_ms * (self._inference_count - 1)) + simulated_ms)
            / self._inference_count
        )
        return detections

    def get_stats(self) -> dict[str, float | int | str]:
        """Return inference performance counters."""
        fps = 0.0
        if self._avg_inference_ms > 0:
            fps = min(float(TARGET_EDGE_FPS), 1000.0 / self._avg_inference_ms)
        return {
            "model_type": self.model_type,
            "runtime": self.runtime,
            "last_inference_ms": round(self._last_inference_ms, 3),
            "avg_inference_ms": round(self._avg_inference_ms, 3),
            "inference_count": self._inference_count,
            "target_fps": TARGET_EDGE_FPS,
            "effective_fps": round(fps, 3),
            "dropped_frames": self._dropped_frames,
        }
