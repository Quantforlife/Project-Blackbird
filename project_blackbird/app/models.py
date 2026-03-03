"""Database models for Project Blackbird."""
from __future__ import annotations

from datetime import datetime

from .extensions import db


class Flight(db.Model):
    """A drone inspection flight."""

    __tablename__ = "flights"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(32), nullable=False, default="uploaded")

    images = db.relationship(
        "Image",
        backref="flight",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    detections = db.relationship(
        "Detection",
        backref="flight",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reports = db.relationship(
        "Report",
        backref="flight",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Image(db.Model):
    """Uploaded image associated with a flight."""

    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey("flights.id", ondelete="CASCADE"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    captured_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    detections = db.relationship(
        "Detection",
        backref="image",
        lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Detection(db.Model):
    """Defect detection result for a given image."""

    __tablename__ = "detections"

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey("flights.id", ondelete="CASCADE"), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    defect_type = db.Column(db.String(120), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)


class Report(db.Model):
    """Generated PDF report."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey("flights.id", ondelete="CASCADE"), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Waitlist(db.Model):
    """Waitlist entries from landing page."""

    __tablename__ = "waitlist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    company = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
