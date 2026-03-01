"""Offline boot tests that require no third-party deps."""
from __future__ import annotations

from app import create_app


def test_basic_boot_routes_return_200():
    app = create_app("testing")
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.get("/flights").status_code == 200
