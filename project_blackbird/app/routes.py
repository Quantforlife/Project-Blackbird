"""Compatibility module for route blueprint imports."""
from app.blueprints.admin import admin_bp
from app.blueprints.api import api_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.realtime import realtime_bp

__all__ = ["api_bp", "dashboard_bp", "admin_bp", "realtime_bp"]
