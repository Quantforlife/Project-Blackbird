"""Pytest fixtures."""
from __future__ import annotations

import io
import tempfile
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app

try:
    from app.extensions import db
except Exception:
    db = None


@pytest.fixture()
def app():
    app_obj = create_app("testing")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        app_obj.config.update(
            UPLOAD_FOLDER=str(root / "uploads"),
            REPORT_FOLDER=str(root / "reports"),
            API_KEY="test-key",
            TESTING=True,
            OFFLINE_MODE=True,
        )
        if db is not None and hasattr(app_obj, "app_context"):
            with app_obj.app_context():
                db.drop_all()
                db.create_all()
                yield app_obj
                db.session.remove()
                db.drop_all()
        else:
            yield app_obj


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_image_bytes() -> io.BytesIO:
    # Minimal JPEG byte stream; avoids external image libs.
    stream = io.BytesIO(
        b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xFF\xDB\x00C\x00" + (b"\x08" * 64) + b"\xFF\xD9"
    )
    stream.seek(0)
    return stream
