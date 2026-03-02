"""Application entrypoint."""
from __future__ import annotations

import os

from app import create_app

config_name = os.getenv("FLASK_ENV", "development")
if config_name not in {"development", "testing", "production"}:
    config_name = "development"

app = create_app(config_name=config_name)

if __name__ == "__main__":
    if hasattr(app, "run"):
        port = int(os.getenv("PORT", "5000"))
        debug = config_name == "development"
        app.run(host="0.0.0.0", port=port, debug=debug)
    else:
        print("Project Blackbird offline fallback app initialized")
