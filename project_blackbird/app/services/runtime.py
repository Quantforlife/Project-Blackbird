"""Runtime service registry and lifecycle helpers."""
from __future__ import annotations

from threading import Lock

from app.interface.controller_bridge import ControllerBridge
from app.interface.socket_server import SocketServerBridge
from app.realtime.controller import RealTimeController
from app.realtime.telemetry import TelemetryEngine
from app.simulation.engine import SimulationEngine

_engine: TelemetryEngine | None = None
_runtime_bridge: ControllerBridge | None = None
_runtime_lock = Lock()


def get_engine(offline_mode: bool = True) -> TelemetryEngine:
    global _engine
    with _runtime_lock:
        if _engine is None:
            _engine = TelemetryEngine(offline_mode=offline_mode)
        return _engine


def get_controller_bridge(diagnostics_enabled: bool = False) -> ControllerBridge:
    global _runtime_bridge
    with _runtime_lock:
        if _runtime_bridge is None:
            simulation_engine = SimulationEngine()
            controller = RealTimeController(
                simulation_engine=simulation_engine,
                event_bus=simulation_engine.event_bus,
                diagnostics_enabled=diagnostics_enabled,
            )
            socket_bridge = SocketServerBridge(
                event_bus=simulation_engine.event_bus,
                diagnostics_enabled=diagnostics_enabled,
            )
            _runtime_bridge = ControllerBridge(
                controller,
                socket_bridge,
                diagnostics_enabled=diagnostics_enabled,
            )
        return _runtime_bridge


def initialize_runtime(app) -> ControllerBridge:
    """Initialize singleton runtime services and bind to app."""
    diagnostics_enabled = app.config.get("DEBUG_DIAGNOSTICS", False)
    bridge = get_controller_bridge(diagnostics_enabled=diagnostics_enabled)
    bridge.socket_bridge.init_app(app)
    bridge.initialize()

    engine = get_engine(offline_mode=app.config.get("OFFLINE_MODE", True))
    engine.start()

    app.extensions["blackbird_controller_bridge"] = bridge
    app.extensions["blackbird_socket_bridge"] = bridge.socket_bridge

    if app.config.get("INVESTOR_DEMO_MODE", False):
        bridge.start_live()
    return bridge


def shutdown_runtime() -> None:
    """Gracefully shutdown background loops and subscribers."""
    with _runtime_lock:
        if _runtime_bridge is not None:
            _runtime_bridge.shutdown()
        if _engine is not None:
            _engine.stop()
