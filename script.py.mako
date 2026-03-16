import os
import uuid
import aiofiles
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Image, Detection, Mission, Drone
from app.schemas.schemas import ImageResponse, DetectionResponse

router = APIRouter(prefix="/images", tags=["images"])


@router.post("", response_model=ImageResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    mission_id: str = Form(...),
    drone_id: str = Form(...),
    lat: float = Form(0.0),
    lon: float = Form(0.0),
    altitude_m: float = Form(0.0),
    heading_deg: float = Form(0.0),
    captured_at: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # Validate references
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    drone = await db.get(Drone, drone_id)
    if not drone:
        raise HTTPException(404, "Drone not found")

    # Save file
    image_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{image_id}{ext}"
    save_dir = os.path.join(settings.upload_dir, "images", mission_id)
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Get image dimensions
    width_px, height_px = None, None
    try:
        from PIL import Image as PILImage
        import io
        img = PILImage.open(io.BytesIO(content))
        width_px, height_px = img.size
    except Exception:
        pass

    ts = datetime.utcnow()
    if captured_at:
        try:
            ts = datetime.fromisoformat(captured_at)
        except Exception:
            pass

    image = Image(
        id=image_id,
        mission_id=mission_id,
        drone_id=drone_id,
        filename=filename,
        filepath=filepath,
        lat=lat,
        lon=lon,
        altitude_m=altitude_m,
        heading_deg=heading_deg,
        captured_at=ts,
        width_px=width_px,
        height_px=height_px,
        processed=False,
    )
    db.add(image)
    await db.flush()

    # Trigger async detection task
    try:
        from app.tasks.detection_tasks import run_detection
        run_detection.delay(image_id)
    except Exception as e:
        pass  # Worker may not be available in dev

    await db.refresh(image)
    return image


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str, db: AsyncSession = Depends(get_db)):
    image = await db.get(Image, image_id)
    if not image:
        raise HTTPException(404, "Image not found")
    return image


@router.get("/{image_id}/detections", response_model=List[DetectionResponse])
async def get_image_detections(image_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Detection).where(Detection.image_id == image_id)
    )
    return result.scalars().all()


@router.get("/{image_id}/file")
async def serve_image(image_id: str, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    image = await db.get(Image, image_id)
    if not image:
        raise HTTPException(404, "Image not found")
    if not os.path.exists(image.filepath):
        raise HTTPException(404, "Image file not found on disk")
    return FileResponse(image.filepath)
