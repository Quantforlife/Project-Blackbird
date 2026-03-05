"""Application configuration."""
from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def _as_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_KEY = os.getenv("API_KEY", "blackbird-dev-key")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    REPORT_FOLDER = os.getenv("REPORT_FOLDER", str(BASE_DIR / "reports"))
    OFFLINE_MODE = _as_bool(os.getenv("OFFLINE_MODE"), True)
    INVESTOR_DEMO_MODE = _as_bool(os.getenv("INVESTOR_DEMO_MODE"), True)
    DEBUG_DIAGNOSTICS = _as_bool(os.getenv("DEBUG_DIAGNOSTICS"), False)


class DevelopmentConfig(Config):
    """Development configuration using SQLite."""

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'blackbird.db'}"
    )


class TestingConfig(Config):
    """Testing configuration using in-memory SQLite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(Config):
    """Production configuration."""

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///blackbird.db")


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
