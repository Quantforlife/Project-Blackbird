"""Report generation pipeline for flight inspections."""
from __future__ import annotations

from pathlib import Path

from app.extensions import db
from app.models import Detection, Flight, Report


_MINIMAL_PDF = b"%PDF-1.1\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n4 0 obj<</Length 63>>stream\nBT /F1 18 Tf 72 720 Td (Project Blackbird Inspection Report) Tj ET\nendstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n0000000354 00000 n \ntrailer<</Root 1 0 R/Size 6>>\nstartxref\n424\n%%EOF\n"


class ReportGenerator:
    """Create visualization and PDF reports with safe fallbacks."""

    def __init__(self, report_folder: str, offline_mode: bool = False) -> None:
        self.report_folder = Path(report_folder)
        self.report_folder.mkdir(parents=True, exist_ok=True)
        self.offline_mode = offline_mode

    def _load_images(self, flight: Flight) -> list[bytes]:
        images: list[bytes] = []
        for image_record in flight.images:
            path = Path(image_record.filepath)
            if path.exists():
                images.append(path.read_bytes())
        return images

    def _write_pdf_fallback(self, pdf_path: Path) -> None:
        pdf_path.write_bytes(_MINIMAL_PDF)

    def _try_opencv_report(self, flight: Flight, pdf_path: Path) -> bool:
        if self.offline_mode:
            return False

        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore
            from reportlab.lib.pagesizes import letter  # type: ignore
            from reportlab.pdfgen import canvas  # type: ignore
        except ImportError:
            return False

        frames = []
        for image_record in flight.images:
            frame = cv2.imread(image_record.filepath)
            if frame is not None:
                frames.append(frame)

        if not frames:
            stitched = np.zeros((480, 640, 3), dtype=np.uint8)
        elif len(frames) == 1:
            stitched = frames[0]
        else:
            try:
                stitcher = cv2.Stitcher_create()
                status, pano = stitcher.stitch(frames)
                if status == cv2.Stitcher_OK and pano is not None:
                    stitched = pano
                else:
                    stitched = frames[0]
            except Exception:
                stitched = frames[0]

        for det in Detection.query.filter_by(flight_id=flight.id).all():
            x, y = int(det.x), int(det.y)
            cv2.circle(stitched, (x, y), 14, (0, 0, 255), 2)

        preview_path = self.report_folder / f"flight_{flight.id}_preview.jpg"
        cv2.imwrite(str(preview_path), stitched)

        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.setTitle(f"Flight {flight.id} Inspection Report")
        c.setFont("Helvetica-Bold", 16)
        c.drawString(36, 760, f"Inspection Report - Flight #{flight.id}")
        c.setFont("Helvetica", 10)
        c.drawString(36, 742, f"Location: {flight.location}")
        c.drawString(36, 728, f"Status: {flight.status}")

        if preview_path.exists():
            c.drawImage(str(preview_path), 36, 340, width=520, height=360, preserveAspectRatio=True)

        c.showPage()
        c.save()
        return True

    def generate(self, flight_id: int) -> Report:
        flight = Flight.query.get_or_404(flight_id)
        self._load_images(flight)

        pdf_path = self.report_folder / f"flight_{flight_id}_report.pdf"
        created = self._try_opencv_report(flight, pdf_path)
        if not created:
            self._write_pdf_fallback(pdf_path)

        report = Report(flight_id=flight_id, file_path=str(pdf_path))
        db.session.add(report)
        db.session.commit()
        return report
