from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.redis_client import publish_event
from app.models.models import Mission, MissionDrone, Drone, DroneStatus, MissionStatus
from app.schemas.schemas import MissionCreate, MissionResponse, MissionAnalytics

router = APIRouter(prefix="/missions", tags=["missions"])


@router.post("", response_model=MissionResponse, status_code=201)
async def create_mission(payload: MissionCreate, db: AsyncSession = Depends(get_db)):
    mission_id = str(uuid.uuid4())
    mission = Mission(
        id=mission_id,
        name=payload.name,
        description=payload.description,
        site_name=payload.site_name,
        waypoints=[w.model_dump() for w in payload.waypoints],
        area_polygon=payload.area_polygon,
        config=payload.config,
    )
    db.add(mission)

    # Assign drones
    for drone_id in payload.drone_ids:
        drone = await db.get(Drone, drone_id)
        if not drone:
            raise HTTPException(404, f"Drone {drone_id} not found")
        md = MissionDrone(
            id=str(uuid.uuid4()),
            mission_id=mission_id,
            drone_id=drone_id,
        )
        db.add(md)

    await db.flush()
    await db.refresh(mission)

    resp = _to_response(mission, payload.drone_ids)
    await publish_event("events:missions", {"type": "mission_created", "mission_id": mission_id})
    return resp


@router.get("", response_model=List[MissionResponse])
async def list_missions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Mission).order_by(Mission.created_at.desc()))
    missions = result.scalars().all()
    out = []
    for m in missions:
        drone_ids = await _get_drone_ids(m.id, db)
        out.append(_to_response(m, drone_ids))
    return out


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    drone_ids = await _get_drone_ids(mission_id, db)
    return _to_response(mission, drone_ids)


@router.post("/{mission_id}/start", response_model=MissionResponse)
async def start_mission(mission_id: str, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    if mission.status not in (MissionStatus.PENDING, MissionStatus.PAUSED):
        raise HTTPException(400, f"Cannot start mission in status: {mission.status}")
    mission.status = MissionStatus.ACTIVE
    mission.started_at = datetime.utcnow()
    db.add(mission)

    # Update assigned drones to flying
    drone_ids = await _get_drone_ids(mission_id, db)
    for did in drone_ids:
        drone = await db.get(Drone, did)
        if drone:
            drone.status = DroneStatus.FLYING
            db.add(drone)

    await db.flush()
    await publish_event("events:missions", {
        "type": "mission_started",
        "mission_id": mission_id,
        "drone_ids": drone_ids,
    })
    return _to_response(mission, drone_ids)


@router.post("/{mission_id}/pause", response_model=MissionResponse)
async def pause_mission(mission_id: str, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    if mission.status != MissionStatus.ACTIVE:
        raise HTTPException(400, "Mission is not active")
    mission.status = MissionStatus.PAUSED
    db.add(mission)
    await db.flush()
    await publish_event("events:missions", {"type": "mission_paused", "mission_id": mission_id})
    drone_ids = await _get_drone_ids(mission_id, db)
    return _to_response(mission, drone_ids)


@router.post("/{mission_id}/stop", response_model=MissionResponse)
async def stop_mission(mission_id: str, db: AsyncSession = Depends(get_db)):
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")
    mission.status = MissionStatus.ABORTED
    mission.completed_at = datetime.utcnow()
    db.add(mission)

    drone_ids = await _get_drone_ids(mission_id, db)
    for did in drone_ids:
        drone = await db.get(Drone, did)
        if drone:
            drone.status = DroneStatus.IDLE
            db.add(drone)

    await db.flush()
    await publish_event("events:missions", {"type": "mission_stopped", "mission_id": mission_id})
    return _to_response(mission, drone_ids)


@router.get("/{mission_id}/analytics", response_model=MissionAnalytics)
async def get_analytics(mission_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    from app.models.models import Image, Detection, AssetInspection, Telemetry

    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(404, "Mission not found")

    img_result = await db.execute(
        select(func.count(Image.id)).where(Image.mission_id == mission_id)
    )
    image_count = img_result.scalar() or 0

    det_result = await db.execute(
        select(Detection).join(Image).where(Image.mission_id == mission_id)
    )
    detections = det_result.scalars().all()

    insp_result = await db.execute(
        select(AssetInspection).where(AssetInspection.mission_id == mission_id)
    )
    inspections = insp_result.scalars().all()

    severity_counts = {}
    type_counts = {}
    for d in detections:
        severity_counts[d.severity.value] = severity_counts.get(d.severity.value, 0) + 1
        type_counts[d.label] = type_counts.get(d.label, 0) + 1

    flight_minutes = 0.0
    if mission.started_at and mission.completed_at:
        delta = mission.completed_at - mission.started_at
        flight_minutes = delta.total_seconds() / 60

    drone_ids = await _get_drone_ids(mission_id, db)
    waypoints = mission.waypoints or []

    return MissionAnalytics(
        mission_id=mission_id,
        total_waypoints=len(waypoints),
        images_captured=image_count,
        defects_found=len(detections),
        coverage_pct=min(100.0, (image_count / max(len(waypoints), 1)) * 100),
        avg_battery_usage=15.0,  # placeholder
        flight_time_minutes=flight_minutes,
        assets_inspected=len(set(i.asset_id for i in inspections)),
        defects_by_severity=severity_counts,
        defects_by_type=type_counts,
    )


# ── Helpers ────────────────────────────────────────────────────────────────

async def _get_drone_ids(mission_id: str, db: AsyncSession):
    result = await db.execute(
        select(MissionDrone.drone_id).where(MissionDrone.mission_id == mission_id)
    )
    return [r[0] for r in result.all()]


def _to_response(mission: Mission, drone_ids: list) -> MissionResponse:
    return MissionResponse(
        id=mission.id,
        name=mission.name,
        description=mission.description,
        status=mission.status,
        site_name=mission.site_name,
        waypoints=mission.waypoints,
        area_polygon=mission.area_polygon,
        config=mission.config,
        started_at=mission.started_at,
        completed_at=mission.completed_at,
        created_at=mission.created_at,
        drone_ids=drone_ids,
    )
