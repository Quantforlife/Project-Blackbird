"""Dashboard and UI routes."""
from __future__ import annotations

from flask import Blueprint, render_template

from app.models import Detection, Flight, Image


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
def home() -> str:
    return render_template("home.html")


@dashboard_bp.get("/dashboard")
def dashboard() -> str:
    total_flights = Flight.query.count()
    total_images = Image.query.count()
    total_defects = Detection.query.count()
    recent_flights = Flight.query.order_by(Flight.started_at.desc()).limit(10).all()
    return render_template(
        "dashboard.html",
        total_flights=total_flights,
        total_images=total_images,
        total_defects=total_defects,
        recent_flights=recent_flights,
    )


@dashboard_bp.get("/flights")
def flights() -> str:
    all_flights = Flight.query.order_by(Flight.started_at.desc()).all()
    return render_template("flights.html", flights=all_flights)


@dashboard_bp.get("/flight/<int:id>")
def flight_detail(id: int) -> str:
    flight = Flight.query.get_or_404(id)
    detections = Detection.query.filter_by(flight_id=id).all()
    defects_by_type: dict[str, int] = {}
    for item in detections:
        defects_by_type[item.defect_type] = defects_by_type.get(item.defect_type, 0) + 1

    markers = [
        {
            "lat": img.latitude if img.latitude is not None else 0.0,
            "lon": img.longitude if img.longitude is not None else 0.0,
            "label": img.filename,
        }
        for img in flight.images
    ]
    return render_template(
        "flight_detail.html",
        flight=flight,
        detections=detections,
        defects_by_type=defects_by_type,
        markers=markers,
    )
