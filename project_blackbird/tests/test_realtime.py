"""Real-time synchronization layer tests."""
from __future__ import annotations

import time

from app.realtime.controller import RealTimeController
from app.realtime.events import (
    BATTERY_UPDATE,
    DETECTION_CONFIRMED,
    EventBus,
    FRAME_CAPTURED,
    MISSION_COMPLETE,
    MISSION_PROGRESS,
    TELEMETRY_UPDATE,
)
from app.realtime.timeline import MissionTimeline
from app.simulation.engine import SimulationEngine


def test_event_bus_subscribe_emit_unsubscribe() -> None:
    bus = EventBus()
    events: list[dict[str, object]] = []

    def callback(payload: dict[str, object]) -> None:
        events.append(payload)

    bus.subscribe(TELEMETRY_UPDATE, callback)
    bus.emit(TELEMETRY_UPDATE, {"value": 1})
    time.sleep(0.05)
    bus.unsubscribe(TELEMETRY_UPDATE, callback)
    bus.emit(TELEMETRY_UPDATE, {"value": 2})
    time.sleep(0.05)
    bus.shutdown()

    assert len(events) == 1
    assert events[0]["value"] == 1


def test_timeline_order_and_seek() -> None:
    timeline = MissionTimeline(max_history_length=10)
    timeline.add({"timestamp": 1.0, "telemetry": {}, "perception_stats": {}, "confirmed_detections": [], "mission_progress": 1.0, "battery": 99.0, "current_waypoint_index": 1})
    timeline.add({"timestamp": 2.0, "telemetry": {}, "perception_stats": {}, "confirmed_detections": [], "mission_progress": 2.0, "battery": 98.0, "current_waypoint_index": 2})

    state = timeline.get_state_at(1.6)
    assert state is not None
    assert state["timestamp"] == 1.0
    assert timeline.duration() == 1.0


def test_engine_emits_structured_events_and_mission_complete_once() -> None:
    bus = EventBus()
    counters = {
        TELEMETRY_UPDATE: 0,
        FRAME_CAPTURED: 0,
        DETECTION_CONFIRMED: 0,
        MISSION_PROGRESS: 0,
        BATTERY_UPDATE: 0,
        MISSION_COMPLETE: 0,
    }

    for event_type in counters:
        bus.subscribe(event_type, lambda payload, et=event_type: counters.__setitem__(et, counters[et] + 1))

    engine = SimulationEngine(rows=1, columns=2, panel_spacing_meters=4.0, velocity_mps=8.0, event_bus=bus)
    for _ in range(20):
        engine.step(1.0)

    time.sleep(0.1)
    bus.shutdown()

    assert counters[TELEMETRY_UPDATE] > 0
    assert counters[FRAME_CAPTURED] > 0
    assert counters[MISSION_PROGRESS] > 0
    assert counters[BATTERY_UPDATE] > 0
    assert counters[MISSION_COMPLETE] == 1


def test_realtime_controller_live_and_playback_modes() -> None:
    bus = EventBus()
    engine = SimulationEngine(rows=2, columns=2, panel_spacing_meters=4.0, velocity_mps=8.0, event_bus=bus)
    controller = RealTimeController(
        simulation_engine=engine,
        event_bus=bus,
        tick_seconds=0.01,
        max_history_length=100,
    )

    controller.start_live()
    time.sleep(0.08)
    controller.pause()
    snapshots = controller.timeline.get_all()
    assert len(snapshots) > 0

    controller.start_playback()
    assert controller.playback_mode is True
    assert controller.live_mode is False

    seek_ts = snapshots[len(snapshots) // 2]["timestamp"]
    state_at = controller.seek(seek_ts)
    assert state_at is not None
    assert state_at["timestamp"] <= seek_ts

    controller.stop()
    bus.shutdown()


def test_playback_reproduces_identical_telemetry_state() -> None:
    bus = EventBus()
    engine = SimulationEngine(rows=2, columns=3, panel_spacing_meters=4.0, velocity_mps=8.0, event_bus=bus)
    controller = RealTimeController(simulation_engine=engine, event_bus=bus, tick_seconds=0.01)

    for _ in range(6):
        engine.step(1.0)
        controller._logical_time = round(controller._logical_time + 1.0, 6)
        controller.timeline.add(controller._compose_snapshot())

    states = controller.timeline.get_all()
    target = states[3]
    replayed = controller.seek(target["timestamp"])

    assert replayed is not None
    assert replayed["telemetry"] == target["telemetry"]
    assert replayed["battery"] == target["battery"]

    bus.shutdown()
