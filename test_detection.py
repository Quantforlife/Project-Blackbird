from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.models import Drone, DroneStatus, Telemetry
from app.schemas.schemas import DroneCreate, DroneResponse, TelemetryResponse

router = APIRouter(prefix="/drones", tags=["drones"])


@router.post("", response_model=DroneResponse, status_code=201)
async def create_drone(payload: DroneCreate, db: AsyncSession = Depends(get_db)):
    drone = Drone(
        id=str(uuid.uuid4()),
        name=payload.name,
        model=payload.model,
        firmware=payload.firmware,
        metadata_=payload.metadata,
    )
    db.add(drone)
    await db.flush()
    await db.refresh(drone)
    return drone


@router.get("", response_model=List[DroneResponse])
async def list_drones(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Drone).order_by(Drone.created_at))
    return result.scalars().all()


@router.get("/{drone_id}", response_model=DroneResponse)
async def get_drone(drone_id: str, db: AsyncSession = Depends(get_db)):
    drone = await db.get(Drone, drone_id)
    if not drone:
        raise HTTPException(404, "Drone not found")
    return drone


@router.get("/{drone_id}/telemetry/latest", response_model=TelemetryResponse)
async def get_latest_telemetry(drone_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Telemetry)
        .where(Telemetry.drone_id == drone_id)
        .order_by(Telemetry.time.desc())
        .limit(1)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(404, "No telemetry found for this drone")
    return t


@router.get("/{drone_id}/telemetry/history", response_model=List[TelemetryResponse])
async def get_telemetry_history(
    drone_id: str,
    limit: int = 500,
    mission_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Telemetry).where(Telemetry.drone_id == drone_id)
    if mission_id:
        q = q.where(Telemetry.mission_id == mission_id)
    q = q.order_by(Telemetry.time.desc()).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/{drone_id}/telemetry", response_model=TelemetryResponse, status_code=201)
async def ingest_telemetry(
    drone_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single telemetry frame (called by simulation)."""
    from app.core.redis_client import publish_telemetry

    drone = await db.get(Drone, drone_id)
    if not drone:
        raise HTTPException(404, "Drone not found")

    t = Telemetry(
        id=str(uuid.uuid4()),
        drone_id=drone_id,
        mission_id=payload.get("mission_id"),
        time=datetime.fromisoformat(payload["time"]) if isinstance(payload.get("time"), str) else datetime.utcnow(),
        lat=payload.get("lat", 0),
        lon=payload.get("lon", 0),
        altitude_m=payload.get("altitude_m", 0),
        heading_deg=payload.get("heading_deg", 0),
        speed_ms=payload.get("speed_ms", 0),
        battery_pct=payload.get("battery_pct", 100),
        roll_deg=payload.get("roll_deg", 0),
        pitch_deg=payload.get("pitch_deg", 0),
        yaw_deg=payload.get("yaw_deg", 0),
        signal_dbm=payload.get("signal_dbm", -60),
        gps_sats=payload.get("gps_sats", 12),
    )
    db.add(t)

    # Update drone position
    drone.lat = t.lat
    drone.lon = t.lon
    drone.altitude_m = t.altitude_m
    drone.battery_pct = t.battery_pct
    drone.last_seen = t.time
    db.add(drone)

    await db.flush()

    # Publish to Redis for WebSocket broadcast
    await publish_telemetry(drone_id, {
        "drone_id": drone_id,
        "time": t.time.isoformat(),
        "lat": t.lat,
        "lon": t.lon,
        "altitude_m": t.altitude_m,
        "heading_deg": t.heading_deg,
        "speed_ms": t.speed_ms,
        "battery_pct": t.battery_pct,
        "roll_deg": t.roll_deg,
        "pitch_deg": t.pitch_deg,
        "yaw_deg": t.yaw_deg,
        "signal_dbm": t.signal_dbm,
    })

    return t
