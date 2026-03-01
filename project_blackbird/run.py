"""Application entrypoint."""
from __future__ import annotations

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    if hasattr(app, "run"):
        port = int(os.getenv("PORT", "5000"))
        app.run(host="0.0.0.0", port=port)
    else:
        print("Project Blackbird offline fallback app initialized")
