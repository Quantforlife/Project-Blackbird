"""Interface bridge tests for socket/event/controller synchronization."""
from __future__ import annotations

import time

from app.interface.controller_bridge import ControllerBridge
from app.interface.socket_server import SocketServerBridge
from app.realtime.controller import RealTimeController
from app.realtime.events import (
    DETECTION_CONFIRMED,
    EventBus,
    MISSION_COMPLETE,
)
from app.simulation.engine import SimulationEngine


class MockSocket:
    """Collect emitted socket events for assertions."""

    def __init__(self) -> None:
        self.emitted: list[tuple[str, dict[str, object]]] = []

    def emit(self, event_name: str, payload: dict[str, object]) -> None:
        self.emitted.append((event_name, payload))

    def init_app(self, _app) -> None:
        return None


def _events(socket: MockSocket, event_name: str) -> list[dict[str, object]]:
    return [payload for name, payload in socket.emitted if name == event_name]


def test_event_bus_to_socket_mapping() -> None:
    bus = EventBus()
    socket = MockSocket()
    bridge = SocketServerBridge(event_bus=bus, socketio=socket)
    bridge.start()

    payload = {
        "timestamp": 1.0,
        "telemetry": {"lat": 1.0, "lon": 2.0, "altitude": 30.0, "heading": 90.0},
        "mission_progress": 10.0,
        "battery": 99.0,
        "current_waypoint_index": 1,
    }
    bus.emit("TELEMETRY_UPDATE", payload)
    bus.emit("TELEMETRY_UPDATE", payload)
    bus.emit("FRAME_CAPTURED", {"timestamp": 1.0, "frame": {"frame_id": 3, "drone_position": {}, "defects_visible": []}, "detections": []})
    time.sleep(0.1)

    bridge.stop()
    bus.shutdown()

    telemetry_events = _events(socket, "telemetry_update")
    frame_events = _events(socket, "frame_update")
    assert len(telemetry_events) == 1
    assert len(frame_events) == 1


def test_controller_commands_start_pause_resume_reset() -> None:
    bus = EventBus()
    socket = MockSocket()
    engine = SimulationEngine(rows=1, columns=3, panel_spacing_meters=4.0, velocity_mps=8.0, event_bus=bus)
    controller = RealTimeController(simulation_engine=engine, event_bus=bus, tick_seconds=0.01)
    socket_bridge = SocketServerBridge(event_bus=bus, socketio=socket)
    bridge = ControllerBridge(controller, socket_bridge)

    bridge.initialize()
    assert bridge.start_live()["status"] == "running"
    time.sleep(0.05)
    assert bridge.pause()["status"] == "paused"
    assert bridge.resume()["status"] == "running"
    time.sleep(0.03)
    assert bridge.reset()["status"] == "reset"

    bridge.shutdown()
    bus.shutdown()


def test_playback_emits_deterministic_telemetry() -> None:
    bus = EventBus()
    socket = MockSocket()
    engine = SimulationEngine(rows=2, columns=2, panel_spacing_meters=4.0, velocity_mps=8.0, event_bus=bus)
    controller = RealTimeController(simulation_engine=engine, event_bus=bus, tick_seconds=0.01)
    socket_bridge = SocketServerBridge(event_bus=bus, socketio=socket)
    bridge = ControllerBridge(controller, socket_bridge)

    for _ in range(4):
        engine.step(1.0)
        controller._logical_time = round(controller._logical_time + 1.0, 6)
        controller.timeline.add(controller._compose_snapshot())

    bridge.start_playback()
    mid = controller.timeline.get_all()[2]["timestamp"]
    state = bridge.seek(mid)

    bridge.shutdown()
    bus.shutdown()

    assert state is not None
    emitted = _events(socket, "telemetry_update")
    assert emitted
    assert emitted[-1]["timestamp"] == state["timestamp"]


def test_mission_complete_and_detection_no_duplicate_spam() -> None:
    bus = EventBus()
    socket = MockSocket()
    bridge = SocketServerBridge(event_bus=bus, socketio=socket)
    bridge.start()

    detection_payload = {
        "timestamp": 2.0,
        "detection": {
            "panel_id": "r0c0",
            "defect_type": "hotspot",
            "geo_location": {"latitude": 1.0, "longitude": 2.0},
        },
    }
    bus.emit(DETECTION_CONFIRMED, detection_payload)
    bus.emit(DETECTION_CONFIRMED, detection_payload)
    bus.emit(MISSION_COMPLETE, {"timestamp": 3.0, "telemetry": {"mission_state": "completed"}})
    time.sleep(0.1)

    bridge.stop()
    bus.shutdown()

    terminal_events = _events(socket, "terminal_event")
    mission_events = _events(socket, "mission_complete")
    assert len(mission_events) == 1
    assert any("Mission complete" in event["message"] for event in terminal_events)
