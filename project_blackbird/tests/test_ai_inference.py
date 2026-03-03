"""Tests for AI inference fallback behavior."""
from __future__ import annotations

from app.utils.ai_inference import AIInference


class _FailingModel:
    def __init__(self) -> None:
        self.calls = 0

    def predict(self, frame):
        self.calls += 1
        raise RuntimeError("backend failure")


def test_infer_uses_deterministic_fallback_when_model_missing():
    inference = AIInference(offline_mode=True)

    detections = inference.infer(frame=None)

    assert len(detections) == 2
    assert detections[0]["defect_type"] == "hotspot"
    assert detections[1]["defect_type"] == "crack"


def test_infer_handles_prediction_errors_without_recursion():
    inference = AIInference(offline_mode=True)
    failing_model = _FailingModel()
    inference.model = failing_model

    detections = inference.infer(frame="any-frame")

    assert failing_model.calls == 1
    assert inference.model is None
    assert len(detections) == 2
    assert detections[0]["defect_type"] == "hotspot"
