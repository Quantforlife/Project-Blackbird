"""Operational real-time controller for live and playback modes."""
from __future__ import annotations

import logging
import threading
import time

from app.realtime.events import MISSION_COMPLETE, TELEMETRY_UPDATE, EventBus
from app.realtime.timeline import MissionTimeline
from app.simulation.engine import SimulationEngine


class RealTimeController:
    """Coordinates live stepping, timeline recording, and deterministic playback."""

    def __init__(
        self,
        simulation_engine: SimulationEngine | None = None,
        event_bus: EventBus | None = None,
        tick_seconds: float = 1.0,
        max_history_length: int = 10_000,
        max_runtime_seconds: float = 600.0,
        diagnostics_enabled: bool = False,
    ) -> None:
        self.engine = simulation_engine or SimulationEngine()
        self.event_bus = event_bus or self.engine.event_bus
        self.timeline = MissionTimeline(max_history_length=max_history_length)
        self.tick_seconds = tick_seconds
        self.max_runtime_seconds = max_runtime_seconds
        self.diagnostics_enabled = diagnostics_enabled
        self.log = logging.getLogger("blackbird.controller")

        self.live_mode = False
        self.playback_mode = False

        self._thread: threading.Thread | None = None
        self._running = False
        self._paused = False
        self._lock = threading.Lock()
        self._logical_time = 0.0
        self._event_cycles = 0

    def _dbg(self, message: str, **data: object) -> None:
        if self.diagnostics_enabled:
            self.log.warning("[controller] %s | %s", message, data)

    def _compose_snapshot(self) -> dict[str, object]:
        state = self.engine.get_current_state()
        return {
            "timestamp": self._logical_time,
            "telemetry": {
                "lat": state["lat"],
                "lon": state["lon"],
                "altitude": state["altitude"],
                "mission_state": state["mission_state"],
            },
            "perception_stats": state["perception_stats"],
            "confirmed_detections": state["confirmed_detections"],
            "mission_progress": state["mission_progress"],
            "battery": state["battery"],
            "current_waypoint_index": state["current_waypoint_index"],
        }

    def _safe_stop(self, reason: str) -> None:
        self._dbg("safe_stop", reason=reason)
        with self._lock:
            self._running = False
            self._paused = False
            self.live_mode = False
            self.playback_mode = False
        self.event_bus.emit(
            MISSION_COMPLETE,
            {
                "timestamp": self._logical_time,
                "reason": reason,
                "telemetry": {"mission_state": "completed"},
            },
        )

    def _run_loop(self) -> None:
        self._dbg("loop_started")
        while True:
            try:
                with self._lock:
                    if not self._running:
                        break
                    should_step = not self._paused

                if should_step:
                    self.engine.step(self.tick_seconds)
                    with self._lock:
                        self._logical_time = round(self._logical_time + self.tick_seconds, 6)
                        self.timeline.add(self._compose_snapshot())
                        self._event_cycles += 1
                        if self._logical_time >= self.max_runtime_seconds:
                            self._safe_stop("max_runtime_reached")
                            break
                time.sleep(self.tick_seconds)
            except Exception as exc:  # runtime failsafe
                self.event_bus.emit(
                    TELEMETRY_UPDATE,
                    {
                        "timestamp": self._logical_time,
                        "telemetry": {"mission_state": "error"},
                        "message": str(exc),
                    },
                )
                self._safe_stop("controller_exception")
                break
        self._dbg("loop_ended")

    def start_live(self) -> tuple[bool, str]:
        """Start or continue live mode updates."""
        with self._lock:
            if self.live_mode and self._running and not self._paused:
                self._dbg("start_blocked", reason="already_running")
                return False, "already_running"
            self.live_mode = True
            self.playback_mode = False
            self._paused = False
            if self._running:
                self._dbg("start_live_resume_existing")
                return True, "resumed"
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            self._dbg("start_live_ok")
            return True, "started"

    def pause(self) -> None:
        with self._lock:
            self._paused = True
        self._dbg("pause")

    def resume(self) -> None:
        with self._lock:
            self._paused = False
        self._dbg("resume")

    def reset(self) -> None:
        self.stop()
        self.engine.reset()
        self.timeline = MissionTimeline(max_history_length=self.timeline.max_history_length)
        self._logical_time = 0.0
        self.live_mode = False
        self.playback_mode = False
        self._event_cycles = 0
        self._dbg("reset")

    def stop(self) -> None:
        with self._lock:
            self._running = False
            self._paused = False
            self.live_mode = False
            self.playback_mode = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
        self._dbg("stop")

    def status(self) -> dict[str, object]:
        with self._lock:
            return {
                "live_mode": self.live_mode,
                "playback_mode": self.playback_mode,
                "running": self._running,
                "paused": self._paused,
                "logical_time": self._logical_time,
                "timeline_size": len(self.timeline.get_all()),
                "event_cycles": self._event_cycles,
            }

    def end(self) -> None:
        self.stop()

    def start_playback(self) -> None:
        self.pause()
        with self._lock:
            self.live_mode = False
            self.playback_mode = True
        self._dbg("start_playback")

    def seek(self, timestamp: float) -> dict[str, object] | None:
        return self.timeline.get_state_at(timestamp)
