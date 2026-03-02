"""Offline boot verification script."""
from __future__ import annotations

import sys

from app import create_app


def main() -> int:
    app = create_app("testing")
    client = app.test_client()

    for path in ("/", "/dashboard", "/flights"):
        response = client.get(path)
        if getattr(response, "status_code", 500) != 200:
            print(f"FAIL: {path} returned {getattr(response, 'status_code', 'unknown')}")
            return 1

    print("SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
