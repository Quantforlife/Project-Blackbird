"""Telemetry engine tests."""
from __future__ import annotations

import time

from app.realtime.telemetry import TelemetryEngine


def test_telemetry_engine_updates() -> None:
    engine = TelemetryEngine(offline_mode=True)
    engine.start()
    engine.command("start")
    try:
        first = engine.snapshot()
        time.sleep(1.2)
        second = engine.snapshot()
    finally:
        engine.stop()

    assert second["flight_time"] >= first["flight_time"]
    assert second["mission_progress"] >= first["mission_progress"]
    assert isinstance(engine.recent_logs(), list)


def test_telemetry_defects_simulate() -> None:
    engine = TelemetryEngine(offline_mode=True)
    engine.start()
    engine.command("start")
    try:
        time.sleep(10.2)
        defects = engine.defect_markers()
    finally:
        engine.stop()
    assert isinstance(defects, list)
