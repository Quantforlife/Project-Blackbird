"""Integration tests for upload and reporting flow."""
from __future__ import annotations

import io
from pathlib import Path

import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_sqlalchemy")


JPEG_BYTES = (
    b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xFF\xDB\x00C\x00" + (b"\x08" * 64) + b"\xFF\xD9"
)


def _jpeg_bytes() -> io.BytesIO:
    return io.BytesIO(JPEG_BYTES)


def test_upload_generate_report_flow(client):
    csv_data = io.BytesIO(
        b"filename,defect_type,confidence,x,y\nimg1.jpg,hotspot,0.99,100,120\nimg2.jpg,crack,0.77,190,140\n"
    )
    upload_response = client.post(
        "/upload",
        headers={"X-API-Key": "test-key"},
        data={
            "name": "Integration Flight",
            "location": "Integration Site",
            "latitude": "40.1",
            "longitude": "-73.2",
            "images": [(_jpeg_bytes(), "img1.jpg"), (_jpeg_bytes(), "img2.jpg")],
            "detections": (csv_data, "detections.csv"),
        },
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    flight_id = upload_response.get_json()["flight_id"]

    report_response = client.post(f"/generate_report/{flight_id}")
    assert report_response.status_code == 200
    report_json = report_response.get_json()
    report_path = Path(report_json["file_path"])
    assert report_path.exists()

    download_response = client.get(f"/report/{report_json['report_id']}")
    assert download_response.status_code == 200
    assert download_response.data.startswith(b"%PDF")
