import { create } from 'zustand';
import type { Drone, Mission, Telemetry, Asset, Detection } from '../types';

interface BlackbirdState {
  // Fleet
  drones: Drone[];
  setDrones: (drones: Drone[]) => void;
  updateDrone: (id: string, patch: Partial<Drone>) => void;

  // Live telemetry — keyed by drone_id
  telemetry: Record<string, Telemetry>;
  updateTelemetry: (t: Telemetry) => void;

  // Missions
  missions: Mission[];
  setMissions: (missions: Mission[]) => void;
  updateMission: (id: string, patch: Partial<Mission>) => void;
  activeMissionId: string | null;
  setActiveMissionId: (id: string | null) => void;

  // Assets
  assets: Asset[];
  setAssets: (assets: Asset[]) => void;

  // Recent detections feed
  recentDetections: Detection[];
  addDetection: (d: Detection) => void;

  // WebSocket status
  wsConnected: boolean;
  setWsConnected: (v: boolean) => void;

  // System events log
  events: { id: number; ts: string; type: string; message: string; level: string }[];
  addEvent: (type: string, message: string, level?: string) => void;
}

let eventId = 0;

export const useStore = create<BlackbirdState>((set) => ({
  drones: [],
  setDrones: (drones) => set({ drones }),
  updateDrone: (id, patch) =>
    set((s) => ({
      drones: s.drones.map((d) => (d.id === id ? { ...d, ...patch } : d)),
    })),

  telemetry: {},
  updateTelemetry: (t) =>
    set((s) => ({
      telemetry: { ...s.telemetry, [t.drone_id]: t },
    })),

  missions: [],
  setMissions: (missions) => set({ missions }),
  updateMission: (id, patch) =>
    set((s) => ({
      missions: s.missions.map((m) => (m.id === id ? { ...m, ...patch } : m)),
    })),
  activeMissionId: null,
  setActiveMissionId: (id) => set({ activeMissionId: id }),

  assets: [],
  setAssets: (assets) => set({ assets }),

  recentDetections: [],
  addDetection: (d) =>
    set((s) => ({
      recentDetections: [d, ...s.recentDetections].slice(0, 50),
    })),

  wsConnected: false,
  setWsConnected: (v) => set({ wsConnected: v }),

  events: [],
  addEvent: (type, message, level = 'info') =>
    set((s) => ({
      events: [
        { id: eventId++, ts: new Date().toISOString(), type, message, level },
        ...s.events,
      ].slice(0, 200),
    })),
}));
