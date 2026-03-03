window.BlackbirdSocketClient = (() => {
  let socket = null;
  let eventSource = null;
  const listeners = new Map();
  let initialized = false;

  const attachSocketListeners = () => {
    listeners.forEach((callbacks, eventName) => {
      callbacks.forEach((cb) => socket.on(eventName, cb));
    });
  };

  const fallbackToSSE = () => {
    if (eventSource) {
      return;
    }
    eventSource = new EventSource('/realtime/stream');
    eventSource.addEventListener('telemetry', (event) => {
      const payload = JSON.parse(event.data);
      emitLocal('telemetry_update', {
        timestamp: payload.telemetry.flight_time || 0,
        latitude: payload.telemetry.latitude,
        longitude: payload.telemetry.longitude,
        altitude: payload.telemetry.altitude,
        heading: payload.telemetry.heading,
        battery: payload.telemetry.battery,
        mission_progress: payload.telemetry.mission_progress,
        waypoint_index: payload.telemetry.images_captured || 0,
      });
      emitLocal('frame_update', {
        frame_id: payload.video?.frame_id || 0,
        drone_pose: payload.telemetry,
        detections: payload.video?.boxes || [],
      });
      emitLocal('mission_progress', {
        timestamp: payload.telemetry.flight_time || 0,
        mission_progress: payload.telemetry.mission_progress,
        current_waypoint_index: payload.telemetry.images_captured || 0,
      });
      emitLocal('battery_update', {
        timestamp: payload.telemetry.flight_time || 0,
        battery: payload.telemetry.battery,
      });
      (payload.logs || []).slice(-1).forEach((line) => {
        emitLocal('terminal_event', {
          timestamp: line.ts || payload.telemetry.timestamp,
          type: line.level || 'SYSTEM',
          message: line.message || String(line),
        });
      });
    });
  };

  const emitLocal = (eventName, payload) => {
    const callbacks = listeners.get(eventName) || [];
    callbacks.forEach((cb) => cb(payload));
  };

  const init = () => {
    if (initialized) {
      return;
    }
    initialized = true;

    if (window.io) {
      socket = window.io({ transports: ['websocket'], reconnection: true, reconnectionAttempts: Infinity });
      attachSocketListeners();
      socket.on('connect_error', () => {
        fallbackToSSE();
      });
      return;
    }
    fallbackToSSE();
  };

  const on = (eventName, callback) => {
    const callbacks = listeners.get(eventName) || [];
    if (!callbacks.includes(callback)) {
      callbacks.push(callback);
      listeners.set(eventName, callbacks);
      if (socket) {
        socket.on(eventName, callback);
      }
    }
  };

  const off = (eventName, callback) => {
    const callbacks = listeners.get(eventName) || [];
    const filtered = callbacks.filter((cb) => cb !== callback);
    listeners.set(eventName, filtered);
    if (socket) {
      socket.off(eventName, callback);
    }
  };

  return { init, on, off };
})();
