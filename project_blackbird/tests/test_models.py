"""Model tests."""
import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_sqlalchemy")

from app.extensions import db
from app.models import Detection, Flight, Image


def test_model_creation(app):
    if not hasattr(app, "app_context"):
        pytest.skip("Fallback app active without SQLAlchemy backend")

    with app.app_context():
        flight = Flight(name="Flight A", location="Farm")
        db.session.add(flight)
        db.session.flush()
        image = Image(flight_id=flight.id, filename="a.jpg", filepath="/tmp/a.jpg")
        db.session.add(image)
        db.session.flush()
        detection = Detection(
            flight_id=flight.id,
            image_id=image.id,
            defect_type="hotspot",
            confidence=0.9,
            x=12,
            y=18,
        )
        db.session.add(detection)
        db.session.commit()

        assert Flight.query.count() == 1
        assert Image.query.count() == 1
        assert Detection.query.count() == 1


def test_relationships(app):
    if not hasattr(app, "app_context"):
        pytest.skip("Fallback app active without SQLAlchemy backend")

    with app.app_context():
        flight = Flight(name="Flight B", location="Array 1")
        db.session.add(flight)
        db.session.flush()
        image = Image(flight_id=flight.id, filename="b.jpg", filepath="/tmp/b.jpg")
        db.session.add(image)
        db.session.flush()
        db.session.add(
            Detection(
                flight_id=flight.id,
                image_id=image.id,
                defect_type="crack",
                confidence=0.8,
                x=1,
                y=2,
            )
        )
        db.session.commit()

        flight_ref = Flight.query.first()
        assert flight_ref is not None
        assert len(flight_ref.images) == 1
        assert len(flight_ref.detections) == 1
