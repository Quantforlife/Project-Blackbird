"""API tests."""
from __future__ import annotations

import io

import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_sqlalchemy")

from app.models import Flight


def test_upload_requires_key(client, sample_image_bytes):
    response = client.post(
        "/upload",
        data={"images": (sample_image_bytes, "sample.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 401


def test_upload_success(client, app):
    img1 = io.BytesIO(
        b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xD9"
    )
    csv_data = io.BytesIO(b"filename,defect_type,confidence,x,y\na.jpg,hotspot,0.91,10,20\n")

    response = client.post(
        "/upload",
        headers={"X-API-Key": "test-key"},
        data={
            "name": "Upload Flight",
            "location": "Farm X",
            "images": (img1, "a.jpg"),
            "detections": (csv_data, "detections.csv"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"

    with app.app_context():
        assert Flight.query.count() == 1


def test_waitlist(client):
    response = client.post("/waitlist", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 201
    assert response.get_json()["message"] == "Added to waitlist"
