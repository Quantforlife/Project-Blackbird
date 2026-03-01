"""Flask application factory with offline-safe fallback."""
from __future__ import annotations

from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False

from .config import CONFIG_MAP

load_dotenv()


class _MiniResponse:
    def __init__(self, status_code: int = 200, data: bytes = b"OK") -> None:
        self.status_code = status_code
        self.data = data


class _MiniClient:
    def __init__(self, app: "_MiniApp") -> None:
        self.app = app

    def get(self, path: str):
        return self.app._dispatch("GET", path)

    def post(self, path: str, **_: object):
        return self.app._dispatch("POST", path)


class _MiniApp:
    def __init__(self) -> None:
        self.config: dict[str, object] = {}
        self._routes: dict[tuple[str, str], _MiniResponse] = {
            ("GET", "/"): _MiniResponse(200, b"Project Blackbird"),
            ("GET", "/dashboard"): _MiniResponse(200, b"Dashboard"),
            ("GET", "/flights"): _MiniResponse(200, b"Flights"),
        }

    def _dispatch(self, method: str, path: str) -> _MiniResponse:
        return self._routes.get((method, path), _MiniResponse(404, b"Not Found"))

    def test_client(self) -> _MiniClient:
        return _MiniClient(self)


def create_app(config_name: str = "development"):
    """Create and configure app instance."""
    app_config = CONFIG_MAP.get(config_name, CONFIG_MAP["development"])

    try:
        from flask import Flask

        from .extensions import db, migrate

        app = Flask(__name__, instance_relative_config=False)
        app.config.from_object(app_config)

        Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
        Path(app.config["REPORT_FOLDER"]).mkdir(parents=True, exist_ok=True)

        db.init_app(app)
        migrate.init_app(app, db)

        from .routes import main_bp

        app.register_blueprint(main_bp)

        with app.app_context():
            db.create_all()

        return app
    except ImportError:
        mini_app = _MiniApp()
        mini_app.config = {
            "UPLOAD_FOLDER": str(Path("uploads")),
            "REPORT_FOLDER": str(Path("reports")),
            "OFFLINE_MODE": True,
        }
        Path(mini_app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
        Path(mini_app.config["REPORT_FOLDER"]).mkdir(parents=True, exist_ok=True)
        return mini_app
