from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from datetime import datetime
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class MissionStatus(str, enum.Enum):
    PENDING   = "pending"
    ACTIVE    = "active"
    PAUSED    = "paused"
    COMPLETED = "completed"
    ABORTED   = "aborted"


class DroneStatus(str, enum.Enum):
    IDLE      = "idle"
    FLYING    = "flying"
    CHARGING  = "charging"
    ERROR     = "error"
    OFFLINE   = "offline"


class AssetType(str, enum.Enum):
    SOLAR_PANEL  = "solar_panel"
    WIND_TURBINE = "wind_turbine"
    POWER_TOWER  = "power_tower"
    SUBSTATION   = "substation"


class DefectSeverity(str, enum.Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class Asset(Base):
    __tablename__ = "assets"

    id              = Column(String, primary_key=True, default=gen_uuid)
    name            = Column(String(128), nullable=False)
    asset_type      = Column(SAEnum(AssetType), nullable=False)
    lat             = Column(Float, nullable=False)
    lon             = Column(Float, nullable=False)
    elevation       = Column(Float, default=0.0)
    orientation     = Column(JSON, default=lambda: {"yaw": 0, "pitch": 0, "roll": 0})
    condition_score = Column(Float, default=100.0)  # 0-100
    install_date    = Column(DateTime, nullable=True)
    metadata_       = Column("metadata", JSON, default=dict)
    created_at      = Column(DateTime, server_default=func.now())
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())

    inspections = relationship("AssetInspection", back_populates="asset")
    detections  = relationship("Detection", back_populates="asset")


class Drone(Base):
    __tablename__ = "drones"

    id           = Column(String, primary_key=True, default=gen_uuid)
    name         = Column(String(64), nullable=False)
    model        = Column(String(64), default="Blackbird-X1")
    status       = Column(SAEnum(DroneStatus), default=DroneStatus.IDLE)
    battery_pct  = Column(Float, default=100.0)
    lat          = Column(Float, nullable=True)
    lon          = Column(Float, nullable=True)
    altitude_m   = Column(Float, default=0.0)
    last_seen    = Column(DateTime, nullable=True)
    firmware     = Column(String(32), default="1.0.0")
    metadata_    = Column("metadata", JSON, default=dict)
    created_at   = Column(DateTime, server_default=func.now())

    telemetry    = relationship("Telemetry", back_populates="drone")
    missions     = relationship("MissionDrone", back_populates="drone")
    images       = relationship("Image", back_populates="drone")


class Mission(Base):
    __tablename__ = "missions"

    id          = Column(String, primary_key=True, default=gen_uuid)
    name        = Column(String(128), nullable=False)
    description = Column(Text, default="")
    status      = Column(SAEnum(MissionStatus), default=MissionStatus.PENDING)
    site_name   = Column(String(128), default="")
    waypoints   = Column(JSON, default=list)   # list of {lat, lon, alt, action}
    area_polygon= Column(JSON, nullable=True)  # GeoJSON polygon
    config      = Column(JSON, default=dict)
    started_at  = Column(DateTime, nullable=True)
    completed_at= Column(DateTime, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())

    drones      = relationship("MissionDrone", back_populates="mission")
    images      = relationship("Image", back_populates="mission")
    inspections = relationship("AssetInspection", back_populates="mission")


class MissionDrone(Base):
    """Association table — drone assigned to a mission."""
    __tablename__ = "mission_drones"

    id         = Column(String, primary_key=True, default=gen_uuid)
    mission_id = Column(String, ForeignKey("missions.id"), nullable=False)
    drone_id   = Column(String, ForeignKey("drones.id"), nullable=False)
    role       = Column(String(32), default="primary")

    mission    = relationship("Mission", back_populates="drones")
    drone      = relationship("Drone", back_populates="missions")


class Telemetry(Base):
    """TimescaleDB hypertable — partitioned by time."""
    __tablename__ = "telemetry"

    id          = Column(String, primary_key=True, default=gen_uuid)
    drone_id    = Column(String, ForeignKey("drones.id"), nullable=False)
    mission_id  = Column(String, ForeignKey("missions.id"), nullable=True)
    time        = Column(DateTime, nullable=False, index=True)
    lat         = Column(Float)
    lon         = Column(Float)
    altitude_m  = Column(Float)
    heading_deg = Column(Float)
    speed_ms    = Column(Float)
    battery_pct = Column(Float)
    roll_deg    = Column(Float, default=0.0)
    pitch_deg   = Column(Float, default=0.0)
    yaw_deg     = Column(Float, default=0.0)
    signal_dbm  = Column(Float, default=-60.0)
    gps_sats    = Column(Integer, default=12)
    metadata_   = Column("metadata", JSON, default=dict)

    drone       = relationship("Drone", back_populates="telemetry")

    __table_args__ = (
        Index("ix_telemetry_drone_time", "drone_id", "time"),
    )


class Image(Base):
    __tablename__ = "images"

    id          = Column(String, primary_key=True, default=gen_uuid)
    mission_id  = Column(String, ForeignKey("missions.id"), nullable=False)
    drone_id    = Column(String, ForeignKey("drones.id"), nullable=False)
    filename    = Column(String(256), nullable=False)
    filepath    = Column(String(512), nullable=False)
    lat         = Column(Float, nullable=True)
    lon         = Column(Float, nullable=True)
    altitude_m  = Column(Float, nullable=True)
    heading_deg = Column(Float, nullable=True)
    captured_at = Column(DateTime, nullable=False)
    width_px    = Column(Integer, nullable=True)
    height_px   = Column(Integer, nullable=True)
    processed   = Column(Boolean, default=False)
    metadata_   = Column("metadata", JSON, default=dict)
    created_at  = Column(DateTime, server_default=func.now())

    mission     = relationship("Mission", back_populates="images")
    drone       = relationship("Drone", back_populates="images")
    detections  = relationship("Detection", back_populates="image")


class Detection(Base):
    __tablename__ = "detections"

    id          = Column(String, primary_key=True, default=gen_uuid)
    image_id    = Column(String, ForeignKey("images.id"), nullable=False)
    asset_id    = Column(String, ForeignKey("assets.id"), nullable=True)
    label       = Column(String(64), nullable=False)
    confidence  = Column(Float, nullable=False)
    severity    = Column(SAEnum(DefectSeverity), default=DefectSeverity.LOW)
    bbox_x      = Column(Float)   # normalized 0-1
    bbox_y      = Column(Float)
    bbox_w      = Column(Float)
    bbox_h      = Column(Float)
    is_manual   = Column(Boolean, default=False)
    notes       = Column(Text, default="")
    created_at  = Column(DateTime, server_default=func.now())

    image       = relationship("Image", back_populates="detections")
    asset       = relationship("Asset", back_populates="detections")


class AssetInspection(Base):
    __tablename__ = "asset_inspections"

    id              = Column(String, primary_key=True, default=gen_uuid)
    asset_id        = Column(String, ForeignKey("assets.id"), nullable=False)
    mission_id      = Column(String, ForeignKey("missions.id"), nullable=False)
    condition_score = Column(Float)
    defect_count    = Column(Integer, default=0)
    notes           = Column(Text, default="")
    inspected_at    = Column(DateTime, server_default=func.now())

    asset   = relationship("Asset", back_populates="inspections")
    mission = relationship("Mission", back_populates="inspections")
