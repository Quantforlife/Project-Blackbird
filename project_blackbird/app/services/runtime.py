"""Runtime service registry."""
from __future__ import annotations

from app.realtime.telemetry import TelemetryEngine

_engine: TelemetryEngine | None = None


def get_engine(offline_mode: bool = True) -> TelemetryEngine:
    global _engine
    if _engine is None:
        _engine = TelemetryEngine(offline_mode=offline_mode)
    return _engine
