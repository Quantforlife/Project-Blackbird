import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Mission

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/{mission_id}")
async def generate_report(
    mission_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")

    try:
        from app.tasks.report_tasks import generate_report as gen
        task = gen.delay(mission_id)
        return {"status": "queued", "task_id": task.id, "mission_id": mission_id}
    except Exception as e:
        # Fallback: generate synchronously
        from app.tasks.report_tasks import generate_report as gen
        result = gen(mission_id)
        return {"status": "ok", "mission_id": mission_id, **result}


@router.get("/{mission_id}/download")
async def download_report(mission_id: str):
    reports_dir = os.path.join(settings.upload_dir, "reports")
    # Find most recent report for this mission
    if not os.path.exists(reports_dir):
        raise HTTPException(404, "No reports found")

    files = [
        f for f in os.listdir(reports_dir)
        if f.startswith(f"report_{mission_id[:8]}")
    ]
    if not files:
        raise HTTPException(404, "Report not yet generated")

    latest = sorted(files)[-1]
    filepath = os.path.join(reports_dir, latest)
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=latest,
    )


@router.get("")
async def list_reports():
    reports_dir = os.path.join(settings.upload_dir, "reports")
    if not os.path.exists(reports_dir):
        return []
    files = []
    for f in sorted(os.listdir(reports_dir), reverse=True):
        if f.endswith(".pdf"):
            fpath = os.path.join(reports_dir, f)
            files.append({
                "filename": f,
                "size_kb": round(os.path.getsize(fpath) / 1024, 1),
                "created_at": os.path.getctime(fpath),
            })
    return files
