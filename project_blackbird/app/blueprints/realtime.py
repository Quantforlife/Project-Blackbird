"""Realtime telemetry and stream routes."""
from __future__ import annotations

import json
import time

from flask import Blueprint, Response, current_app, jsonify

from app.services.runtime import get_engine


realtime_bp = Blueprint("realtime", __name__, url_prefix="/realtime")


def _sse_pack(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


@realtime_bp.get("/snapshot")
def snapshot() -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))
    return jsonify(
        {
            "telemetry": engine.snapshot(),
            "logs": engine.recent_logs(),
            "defects": engine.defect_markers(),
        }
    )


@realtime_bp.get("/stream")
def stream() -> Response:
    engine = get_engine(offline_mode=current_app.config.get("OFFLINE_MODE", True))

    def event_stream():
        while True:
            payload = {
                "telemetry": engine.snapshot(),
                "logs": engine.recent_logs(25),
                "defects": engine.defect_markers(),
            }
            yield _sse_pack("telemetry", payload)
            time.sleep(1)

    return Response(event_stream(), mimetype="text/event-stream")
