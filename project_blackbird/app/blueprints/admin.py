"""Admin routes."""
from __future__ import annotations

from flask import Blueprint, Response, jsonify, render_template, request

from app.extensions import db
from app.models import Waitlist


admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/waitlist")
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


@admin_bp.get("/admin/waitlist")
def waitlist_admin() -> str:
    entries = Waitlist.query.order_by(Waitlist.created_at.desc()).all()
    return render_template("waitlist_admin.html", entries=entries)
