"""HTTP routes for Blackbird MVP."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from .extensions import db
from .models import Detection, Flight, Image, Report, Waitlist
from .utils.data_logger import DataLogger
from .utils.report_generator import ReportGenerator


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def home() -> str:
    return render_template("home.html")


@main_bp.get("/dashboard")
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


@main_bp.post("/upload")
def upload() -> Response:
    api_key = request.headers.get("X-API-Key")
    if api_key != current_app.config["API_KEY"]:
        return jsonify({"error": "Unauthorized"}), 401

    flight_name = request.form.get("name", f"Flight-{datetime.utcnow().isoformat()}")
    location = request.form.get("location", "Unknown")

    flight = Flight(name=flight_name, location=location, status="processed")
    db.session.add(flight)
    db.session.commit()

    logger = DataLogger(current_app.config["UPLOAD_FOLDER"])
    image_files = request.files.getlist("images")
    saved_files = logger.save_images(image_files, flight.id)

    image_map: dict[str, Image] = {}
    for filename, path in saved_files:
        image_record = Image(
            flight_id=flight.id,
            filename=filename,
            filepath=str(path),
            latitude=float(request.form.get("latitude", 0.0)),
            longitude=float(request.form.get("longitude", 0.0)),
        )
        db.session.add(image_record)
        db.session.flush()
        image_map[filename] = image_record

    detections_csv = request.files.get("detections")
    parsed_count = 0
    if detections_csv:
        content = detections_csv.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            filename = row.get("filename", "")
            image_ref = image_map.get(filename)
            if image_ref is None and flight.images:
                image_ref = flight.images[0]
            if image_ref is None:
                continue
            detection = Detection(
                flight_id=flight.id,
                image_id=image_ref.id,
                defect_type=row.get("defect_type", "unknown"),
                confidence=float(row.get("confidence", 0.0)),
                x=float(row.get("x", 0.0)),
                y=float(row.get("y", 0.0)),
            )
            db.session.add(detection)
            parsed_count += 1

    db.session.commit()

    return jsonify(
        {
            "flight_id": flight.id,
            "images": len(saved_files),
            "detections": parsed_count,
            "status": "ok",
        }
    )


@main_bp.get("/flights")
def flights() -> str:
    all_flights = Flight.query.order_by(Flight.started_at.desc()).all()
    return render_template("flights.html", flights=all_flights)


@main_bp.get("/flight/<int:id>")
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


@main_bp.get("/image/<int:id>")
def get_image(id: int):
    image = Image.query.get_or_404(id)
    path = Path(image.filepath)
    if not path.exists():
        return jsonify({"error": "Image missing"}), 404
    return send_file(path)


@main_bp.post("/generate_report/<int:id>")
def generate_report(id: int) -> Response:
    Flight.query.get_or_404(id)
    generator = ReportGenerator(
        current_app.config["REPORT_FOLDER"],
        offline_mode=current_app.config.get("OFFLINE_MODE", False),
    )
    report = generator.generate(id)
    return jsonify({"report_id": report.id, "file_path": report.file_path})


@main_bp.get("/report/<int:id>")
def get_report(id: int):
    report = Report.query.get_or_404(id)
    report_path = Path(report.file_path)
    if not report_path.exists():
        return jsonify({"error": "Report file missing"}), 404
    return send_file(report_path, as_attachment=True)


@main_bp.post("/waitlist")
def add_waitlist() -> Response:
    payload = request.get_json(silent=True) or request.form
    name = payload.get("name")
    email = payload.get("email")
    company = payload.get("company")

    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400

    exists = Waitlist.query.filter_by(email=email).first()
    if exists:
        return jsonify({"message": "Already registered", "id": exists.id}), 200

    entry = Waitlist(name=name, email=email, company=company)
    db.session.add(entry)
    db.session.commit()
    return jsonify({"id": entry.id, "message": "Added to waitlist"}), 201


@main_bp.get("/admin/waitlist")
def waitlist_admin() -> str:
    entries = Waitlist.query.order_by(Waitlist.created_at.desc()).all()
    return render_template("waitlist_admin.html", entries=entries)


@main_bp.get("/health")
def health() -> Response:
    return jsonify({"status": "ok"})


@main_bp.get("/flight/<int:id>/json")
def flight_json(id: int) -> Response:
    flight = Flight.query.get_or_404(id)
    return jsonify(
        {
            "id": flight.id,
            "name": flight.name,
            "location": flight.location,
            "images": [img.filename for img in flight.images],
            "detections": [det.defect_type for det in flight.detections],
        }
    )


@main_bp.post("/seed")
def seed() -> Response:
    flight = Flight(name="Demo Flight", location="Sample Site")
    db.session.add(flight)
    db.session.commit()
    return redirect(url_for("main.flight_detail", id=flight.id))
