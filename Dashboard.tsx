import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '../store';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
const RECONNECT_DELAY = 3000;

export function useFleetWebSocket() {
  const { updateTelemetry, updateDrone, setWsConnected, addEvent } = useStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_URL}/ws/fleet`);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      addEvent('ws', 'Fleet WebSocket connected', 'success');
    };

    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        if (data.type === 'ping') return;
        if (data.drone_id) {
          updateTelemetry(data);
          updateDrone(data.drone_id, {
            lat: data.lat,
            lon: data.lon,
            altitude_m: data.altitude_m,
            battery_pct: data.battery_pct,
            last_seen: data.time,
          });
        }
      } catch {}
    };

    ws.onclose = () => {
      setWsConnected(false);
      addEvent('ws', 'Fleet WebSocket disconnected — reconnecting...', 'warn');
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => {
      addEvent('ws', 'Fleet WebSocket error', 'error');
      ws.close();
    };
  }, [updateTelemetry, updateDrone, setWsConnected, addEvent]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);
}

export function useEventsWebSocket() {
  const { addEvent, updateMission, addDetection } = useStore();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_URL}/ws/events`);
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'ping') return;
        const d = msg.data || {};

        switch (d.type) {
          case 'mission_started':
            updateMission(d.mission_id, { status: 'active' });
            addEvent('mission', `Mission ${d.mission_id?.slice(0, 8)} started`, 'success');
            break;
          case 'mission_paused':
            updateMission(d.mission_id, { status: 'paused' });
            addEvent('mission', `Mission paused`, 'warn');
            break;
          case 'mission_stopped':
            updateMission(d.mission_id, { status: 'aborted' });
            addEvent('mission', `Mission stopped`, 'warn');
            break;
          case 'detection':
            addEvent('detection', `${d.count} defects found in image`, 'error');
            break;
          default:
            break;
        }
      } catch {}
    };

    ws.onclose = () => {
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };
  }, [addEvent, updateMission, addDetection]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
