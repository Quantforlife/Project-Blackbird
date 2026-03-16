from app.tasks.celery_app import celery_app
from app.tasks.detection_tasks import run_detection
from app.tasks.report_tasks import generate_report

__all__ = ["celery_app", "run_detection", "generate_report"]
