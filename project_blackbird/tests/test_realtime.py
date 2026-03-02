"""Realtime endpoint tests."""
from __future__ import annotations

import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_sqlalchemy")


def test_realtime_snapshot(client):
    response = client.get("/realtime/snapshot")
    assert response.status_code == 200
    payload = response.get_json()
    assert "telemetry" in payload
    assert "logs" in payload


def test_realtime_stream(client):
    response = client.get("/realtime/stream")
    assert response.status_code == 200
    chunk = next(iter(response.response)).decode("utf-8")
    assert "event: telemetry" in chunk
