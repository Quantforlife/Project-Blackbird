import axios from 'axios';
import type {
  Mission, Drone, Telemetry, DroneImage,
  Detection, Asset, AssetInspection, MissionAnalytics,
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ── Missions ─────────────────────────────────────────────────────────────────
export const getMissions = () => api.get<Mission[]>('/missions').then(r => r.data);
export const getMission = (id: string) => api.get<Mission>(`/missions/${id}`).then(r => r.data);
export const createMission = (payload: any) => api.post<Mission>('/missions', payload).then(r => r.data);
export const startMission = (id: string) => api.post<Mission>(`/missions/${id}/start`).then(r => r.data);
export const pauseMission = (id: string) => api.post<Mission>(`/missions/${id}/pause`).then(r => r.data);
export const stopMission  = (id: string) => api.post<Mission>(`/missions/${id}/stop`).then(r => r.data);
export const getMissionAnalytics = (id: string) => api.get<MissionAnalytics>(`/missions/${id}/analytics`).then(r => r.data);
export const getMissionImages = (id: string) => api.get<DroneImage[]>(`/missions/${id}/images`).then(r => r.data);

// ── Drones ────────────────────────────────────────────────────────────────────
export const getDrones = () => api.get<Drone[]>('/drones').then(r => r.data);
export const getDrone  = (id: string) => api.get<Drone>(`/drones/${id}`).then(r => r.data);
export const getLatestTelemetry = (id: string) => api.get<Telemetry>(`/drones/${id}/telemetry/latest`).then(r => r.data);
export const getTelemetryHistory = (id: string, limit = 200) =>
  api.get<Telemetry[]>(`/drones/${id}/telemetry/history?limit=${limit}`).then(r => r.data);

// ── Images ────────────────────────────────────────────────────────────────────
export const getImage = (id: string) => api.get<DroneImage>(`/images/${id}`).then(r => r.data);
export const getImageDetections = (id: string) => api.get<Detection[]>(`/images/${id}/detections`).then(r => r.data);
export const getImageUrl = (id: string) => `${API_URL}/images/${id}/file`;

// ── Detections ────────────────────────────────────────────────────────────────
export const getDetections = (params?: { mission_id?: string; label?: string; severity?: string }) =>
  api.get<Detection[]>('/detections', { params }).then(r => r.data);
export const createDetection = (payload: any) => api.post<Detection>('/detections', payload).then(r => r.data);
export const updateDetection = (id: string, payload: any) => api.put<Detection>(`/detections/${id}`, payload).then(r => r.data);
export const deleteDetection = (id: string) => api.delete(`/detections/${id}`);

// ── Assets ────────────────────────────────────────────────────────────────────
export const getAssets = () => api.get<Asset[]>('/assets').then(r => r.data);
export const getAsset  = (id: string) => api.get<Asset>(`/assets/${id}`).then(r => r.data);
export const getAssetHistory = (id: string) => api.get<AssetInspection[]>(`/assets/${id}/history`).then(r => r.data);
export const createAsset = (payload: any) => api.post<Asset>('/assets', payload).then(r => r.data);

// ── Reports ───────────────────────────────────────────────────────────────────
export const generateReport = (mission_id: string) => api.post(`/reports/${mission_id}`).then(r => r.data);
export const listReports = () => api.get<any[]>('/reports').then(r => r.data);
export const getReportDownloadUrl = (mission_id: string) => `${API_URL}/reports/${mission_id}/download`;
