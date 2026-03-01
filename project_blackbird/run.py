"""Application entrypoint."""
from __future__ import annotations

from app import create_app

app = create_app()

if __name__ == "__main__":
    if hasattr(app, "run"):
        app.run(host="0.0.0.0", port=5000)
    else:
        print("Project Blackbird offline fallback app initialized")
