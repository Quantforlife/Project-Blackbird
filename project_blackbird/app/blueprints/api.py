"""API routes."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, request, send_file

from app.extensions import db
from app.models import Detection, Flight, Image, Report
from app.utils.data_logger import DataLogger
from app.utils.report_generator import ReportGenerator


api_bp = Blueprint("api", __name__)


@api_bp.post("/upload")
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
            image_ref = image_map.get(row.get("filename", ""))
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
    return jsonify({"flight_id": flight.id, "images": len(saved_files), "detections": parsed_count, "status": "ok"})


@api_bp.post("/generate_report/<int:id>")
def generate_report(id: int) -> Response:
    Flight.query.get_or_404(id)
    generator = ReportGenerator(
        current_app.config["REPORT_FOLDER"],
        offline_mode=current_app.config.get("OFFLINE_MODE", False),
    )
    report = generator.generate(id)
    return jsonify({"report_id": report.id, "file_path": report.file_path})


@api_bp.get("/report/<int:id>")
def get_report(id: int):
    report = Report.query.get_or_404(id)
    report_path = Path(report.file_path)
    if not report_path.exists():
        return jsonify({"error": "Report file missing"}), 404
    return send_file(report_path, as_attachment=True)


@api_bp.get("/image/<int:id>")
def get_image(id: int):
    image = Image.query.get_or_404(id)
    path = Path(image.filepath)
    if not path.exists():
        return jsonify({"error": "Image missing"}), 404
    return send_file(path)


@api_bp.get("/health")
def health() -> Response:
    return jsonify({"status": "ok"})
