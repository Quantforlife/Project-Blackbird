"""Realtime telemetry and stream routes."""
from __future__ import annotations

import json
import time

from flask import Blueprint, Response, current_app, jsonify, request

from app.services.runtime import get_engine


realtime_bp = Blueprint("realtime", __name__, url_prefix="/realtime")


def _sse_pack(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def _payload(engine) -> dict:
    defects = engine.defect_markers()
    critical = len([d for d in defects if d.get("severity") == "critical"])
    warning = len([d for d in defects if d.get("severity") == "warning"])
    minor = len([d for d in defects if d.get("severity") == "minor"])
    return {
        "telemetry": engine.snapshot(),
        "logs": engine.recent_logs(60),
        "defects": defects,
        "path": engine.path_points(),
        "video": engine.video_payload(),
        "analytics": {
            "critical": critical,
            "warning": warning,
            "minor": minor,
            "total": len(defects),
        },
    }


@realtime_bp.get("/snapshot")
def snapshot() -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))
    return jsonify(_payload(engine))


@realtime_bp.get("/stream")
def stream() -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))

    def event_stream():
        while True:
            yield _sse_pack("telemetry", _payload(engine))
            time.sleep(1)

    return Response(event_stream(), mimetype="text/event-stream")


@realtime_bp.post("/command/<action>")
def command(action: str) -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))
    return jsonify(engine.command(action))


@realtime_bp.post("/mode/<mode>")
def mode(mode: str) -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))
    return jsonify(engine.set_mode(mode))


@realtime_bp.post("/playback/<int:index>")
def playback(index: int) -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))
    return jsonify(engine.set_playback_index(index))


@realtime_bp.get("/video")
def video() -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))
    return jsonify(engine.video_payload())
