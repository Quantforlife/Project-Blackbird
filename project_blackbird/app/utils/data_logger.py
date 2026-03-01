"""Data logging helpers for onboard capture payloads."""
from __future__ import annotations

import csv
from pathlib import Path
import zipfile

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class DataLogger:
    """Utility class to save mission data artifacts."""

    def __init__(self, upload_folder: str) -> None:
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(parents=True, exist_ok=True)

    def save_images(self, files: list[FileStorage], flight_id: int) -> list[tuple[str, Path]]:
        saved: list[tuple[str, Path]] = []
        flight_dir = self.upload_folder / f"flight_{flight_id}"
        flight_dir.mkdir(parents=True, exist_ok=True)
        for item in files:
            filename = secure_filename(item.filename or "image.jpg")
            target = flight_dir / filename
            item.save(target)
            saved.append((filename, target))
        return saved

    def append_csv(self, csv_path: str | Path, rows: list[dict[str, str | float | int]]) -> None:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            return
        write_header = not csv_path.exists()
        with csv_path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            if write_header:
                writer.writeheader()
            writer.writerows(rows)

    def create_zip_package(self, flight_id: int) -> Path:
        flight_dir = self.upload_folder / f"flight_{flight_id}"
        zip_path = self.upload_folder / f"flight_{flight_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in flight_dir.glob("**/*"):
                if file_path.is_file():
                    archive.write(file_path, arcname=file_path.relative_to(flight_dir))
        return zip_path
