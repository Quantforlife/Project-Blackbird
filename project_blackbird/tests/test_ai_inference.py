"""Tests for AI inference fallback behavior."""
from __future__ import annotations

from app.utils.ai_inference import AIInference


class _FailingModel:
    def __init__(self) -> None:
        self.calls = 0

    def predict(self, _frame):
        self.calls += 1
        raise RuntimeError("backend failure")


def test_infer_uses_safe_fallback_on_predict_error():
    engine = AIInference(offline_mode=True)
    failing_model = _FailingModel()
    engine.model = failing_model

    detections = engine.infer(frame=object())

    assert failing_model.calls == 1
    assert engine.model is None
    assert detections == [
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
