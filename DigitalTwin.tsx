// ─── Enums ──────────────────────────────────────────────────────────────────

export type MissionStatus = 'pending' | 'active' | 'paused' | 'completed' | 'aborted';
export type DroneStatus   = 'idle' | 'flying' | 'charging' | 'error' | 'offline';
export type AssetType     = 'solar_panel' | 'wind_turbine' | 'power_tower' | 'substation';
export type DefectSeverity = 'low' | 'medium' | 'high' | 'critical';

// ─── Core models ────────────────────────────────────────────────────────────

export interface Waypoint {
  lat: number;
  lon: number;
  alt: number;
  action: string;
  hover_seconds: number;
}

export interface Mission {
  id: string;
  name: string;
  description: string;
  status: MissionStatus;
  site_name: string;
  waypoints: Waypoint[];
  area_polygon: any | null;
  config: Record<string, any>;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  drone_ids: string[];
}

export interface Drone {
  id: string;
  name: string;
  model: string;
  status: DroneStatus;
  battery_pct: number;
  lat: number | null;
  lon: number | null;
  altitude_m: number;
  last_seen: string | null;
  firmware: string;
  created_at: string;
}

export interface Telemetry {
  id?: string;
  drone_id: string;
  mission_id?: string;
  time: string;
  lat: number;
  lon: number;
  altitude_m: number;
  heading_deg: number;
  speed_ms: number;
  battery_pct: number;
  roll_deg: number;
  pitch_deg: number;
  yaw_deg: number;
  signal_dbm: number;
  gps_sats: number;
}

export interface DroneImage {
  id: string;
  mission_id: string;
  drone_id: string;
  filename: string;
  filepath: string;
  lat: number | null;
  lon: number | null;
  altitude_m: number | null;
  heading_deg: number | null;
  captured_at: string;
  processed: boolean;
  width_px: number | null;
  height_px: number | null;
  created_at: string;
}

export interface Detection {
  id: string;
  image_id: string;
  asset_id: string | null;
  label: string;
  confidence: number;
  severity: DefectSeverity;
  bbox_x: number;
  bbox_y: number;
  bbox_w: number;
  bbox_h: number;
  is_manual: boolean;
  notes: string;
  created_at: string;
}

export interface Asset {
  id: string;
  name: string;
  asset_type: AssetType;
  lat: number;
  lon: number;
  elevation: number;
  orientation: { yaw: number; pitch: number; roll: number };
  condition_score: number;
  install_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetInspection {
  id: string;
  asset_id: string;
  mission_id: string;
  condition_score: number;
  defect_count: number;
  notes: string;
  inspected_at: string;
}

export interface MissionAnalytics {
  mission_id: string;
  total_waypoints: number;
  images_captured: number;
  defects_found: number;
  coverage_pct: number;
  avg_battery_usage: number;
  flight_time_minutes: number;
  assets_inspected: number;
  defects_by_severity: Record<string, number>;
  defects_by_type: Record<string, number>;
}

// ─── WebSocket messages ──────────────────────────────────────────────────────

export interface WsFleetMessage extends Telemetry {
  type?: string;
}

export interface WsEventMessage {
  channel: string;
  data: {
    type: string;
    mission_id?: string;
    drone_ids?: string[];
    image_id?: string;
    count?: number;
    timestamp?: string;
  };
}
