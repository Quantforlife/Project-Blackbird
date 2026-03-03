"""Stability and lifecycle tests."""
from __future__ import annotations

import tracemalloc
import time

from app.interface.controller_bridge import ControllerBridge
from app.interface.socket_server import SocketServerBridge
from app.realtime.controller import RealTimeController
from app.realtime.events import EventBus, TELEMETRY_UPDATE
from app.realtime.timeline import MissionTimeline
from app.simulation.engine import SimulationEngine


class MockSocket:
    def __init__(self) -> None:
        self.emitted: list[tuple[str, dict[str, object]]] = []

    def emit(self, event_name: str, payload: dict[str, object]) -> None:
        self.emitted.append((event_name, payload))

    def init_app(self, _app) -> None:
        return None


def test_no_duplicate_event_emission() -> None:
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
    bus.emit(TELEMETRY_UPDATE, payload)
    bus.emit(TELEMETRY_UPDATE, payload)
    time.sleep(0.1)

    bridge.stop()
    bus.shutdown()

    telemetry = [name for name, _ in socket.emitted if name == "telemetry_update"]
    assert len(telemetry) == 1


def test_controller_cannot_start_twice() -> None:
    engine = SimulationEngine(rows=1, columns=2)
    controller = RealTimeController(simulation_engine=engine, event_bus=engine.event_bus, tick_seconds=0.01)
    first = controller.start_live()
    second = controller.start_live()
    controller.stop()
    engine.event_bus.shutdown()
    assert first is True
    assert second is False


def test_timeline_retention_enforced() -> None:
    timeline = MissionTimeline(max_history_length=3)
    for i in range(6):
        timeline.add({"timestamp": float(i), "v": i})
    all_items = timeline.get_all()
    assert len(all_items) == 3
    assert all_items[0]["timestamp"] == 3.0


def test_reset_clears_listeners() -> None:
    bus = EventBus()
    socket = MockSocket()
    engine = SimulationEngine(rows=1, columns=2, event_bus=bus)
    controller = RealTimeController(simulation_engine=engine, event_bus=bus, tick_seconds=0.01)
    socket_bridge = SocketServerBridge(event_bus=bus, socketio=socket)
    bridge = ControllerBridge(controller, socket_bridge)

    bridge.initialize()
    assert socket_bridge.subscription_count > 0
    bridge.shutdown()
    assert socket_bridge.subscription_count == 0
    bus.shutdown()


def test_satellite_map_config_loads() -> None:
    text = open("app/static/js/map_renderer.js", encoding="utf-8").read()
    assert "World_Imagery" in text
    assert "tileerror" in text
    assert "map-tile-mode" in open("app/templates/dashboard.html", encoding="utf-8").read()


def test_socket_server_registers_once() -> None:
    bus = EventBus()
    socket = MockSocket()
    bridge = SocketServerBridge(event_bus=bus, socketio=socket)
    bridge.start()
    once = bridge.subscription_count
    bridge.start()
    twice = bridge.subscription_count
    bridge.stop()
    bus.shutdown()
    assert once == twice


def test_long_run_memory_stays_bounded_for_timeline() -> None:
    engine = SimulationEngine(rows=1, columns=3)
    controller = RealTimeController(
        simulation_engine=engine,
        event_bus=engine.event_bus,
        tick_seconds=0.001,
        max_history_length=300,
    )
    tracemalloc.start()
    start_mem = tracemalloc.get_traced_memory()[0]
    for _ in range(1200):
        engine.step(0.01)
        controller._logical_time = round(controller._logical_time + 0.01, 6)
        controller.timeline.add(controller._compose_snapshot())
    end_mem = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    assert len(controller.timeline.get_all()) == 300
    assert end_mem - start_mem < 5_000_000


def test_socket_client_has_reconnect_and_single_init_guards() -> None:
    text = open("app/static/js/socket_client.js", encoding="utf-8").read()
    assert "reconnectionAttempts: Infinity" in text
    assert "if (initialized)" in text
    assert "socket.off(eventName, callback)" in text
