from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models.models import MissionStatus, DroneStatus, AssetType, DefectSeverity


# ─────────────────────────────────────────────
# COMMON
# ─────────────────────────────────────────────

class Waypoint(BaseModel):
    lat: float
    lon: float
    alt: float = 50.0
    action: str = "scan"
    hover_seconds: float = 2.0


# ─────────────────────────────────────────────
# MISSION
# ─────────────────────────────────────────────

class MissionCreate(BaseModel):
    name: str
    description: str = ""
    site_name: str = ""
    waypoints: List[Waypoint] = []
    area_polygon: Optional[Dict] = None
    drone_ids: List[str] = []
    config: Dict[str, Any] = {}


class MissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[MissionStatus] = None


class MissionResponse(BaseModel):
    id: str
    name: str
    description: str
    status: MissionStatus
    site_name: str
    waypoints: List[Any]
    area_polygon: Optional[Dict]
    config: Dict
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    drone_ids: List[str] = []

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# DRONE
# ─────────────────────────────────────────────

class DroneCreate(BaseModel):
    name: str
    model: str = "Blackbird-X1"
    firmware: str = "1.0.0"
    metadata: Dict[str, Any] = {}


class DroneResponse(BaseModel):
    id: str
    name: str
    model: str
    status: DroneStatus
    battery_pct: float
    lat: Optional[float]
    lon: Optional[float]
    altitude_m: float
    last_seen: Optional[datetime]
    firmware: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# TELEMETRY
# ─────────────────────────────────────────────

class TelemetryCreate(BaseModel):
    drone_id: str
    mission_id: Optional[str] = None
    time: datetime
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float = 0.0
    speed_ms: float = 0.0
    battery_pct: float = 100.0
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0
    signal_dbm: float = -60.0
    gps_sats: int = 12
    metadata: Dict[str, Any] = {}


class TelemetryResponse(BaseModel):
    id: str
    drone_id: str
    mission_id: Optional[str]
    time: datetime
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float
    speed_ms: float
    battery_pct: float
    roll_deg: float
    pitch_deg: float
    yaw_deg: float
    signal_dbm: float
    gps_sats: int

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# IMAGE
# ─────────────────────────────────────────────

class ImageResponse(BaseModel):
    id: str
    mission_id: str
    drone_id: str
    filename: str
    filepath: str
    lat: Optional[float]
    lon: Optional[float]
    altitude_m: Optional[float]
    heading_deg: Optional[float]
    captured_at: datetime
    processed: bool
    width_px: Optional[int]
    height_px: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# DETECTION
# ─────────────────────────────────────────────

class DetectionCreate(BaseModel):
    image_id: str
    asset_id: Optional[str] = None
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: DefectSeverity = DefectSeverity.LOW
    bbox_x: float = 0.0
    bbox_y: float = 0.0
    bbox_w: float = 0.0
    bbox_h: float = 0.0
    is_manual: bool = False
    notes: str = ""


class DetectionResponse(BaseModel):
    id: str
    image_id: str
    asset_id: Optional[str]
    label: str
    confidence: float
    severity: DefectSeverity
    bbox_x: float
    bbox_y: float
    bbox_w: float
    bbox_h: float
    is_manual: bool
    notes: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# ASSET
# ─────────────────────────────────────────────

class AssetCreate(BaseModel):
    name: str
    asset_type: AssetType
    lat: float
    lon: float
    elevation: float = 0.0
    orientation: Dict[str, float] = {"yaw": 0, "pitch": 0, "roll": 0}
    install_date: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class AssetResponse(BaseModel):
    id: str
    name: str
    asset_type: AssetType
    lat: float
    lon: float
    elevation: float
    orientation: Dict
    condition_score: float
    install_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetInspectionResponse(BaseModel):
    id: str
    asset_id: str
    mission_id: str
    condition_score: float
    defect_count: int
    notes: str
    inspected_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────

class MissionAnalytics(BaseModel):
    mission_id: str
    total_waypoints: int
    images_captured: int
    defects_found: int
    coverage_pct: float
    avg_battery_usage: float
    flight_time_minutes: float
    assets_inspected: int
    defects_by_severity: Dict[str, int]
    defects_by_type: Dict[str, int]
