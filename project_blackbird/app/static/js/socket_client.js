window.BlackbirdSocketClient = (() => {
  let socket = null;
  let eventSource = null;
  const listeners = new Map();
  let initialized = false;
  let sseStarted = false;
  let diagnostics = false;

  const debug = (...args) => {
    if (diagnostics) {
      console.debug('[BlackbirdSocketClient]', ...args);
    }
  };

  const emitLocal = (eventName, payload) => {
    const callbacks = listeners.get(eventName) || [];
    callbacks.forEach((cb) => cb(payload));
  };

  const setStatus = (status) => {
    debug('connection_status', status, socket ? socket.connected : false);
    emitLocal('connection_status', { status, connected: Boolean(socket && socket.connected) });
  };

  const bindSocketEvents = () => {
    if (!socket) return;
    listeners.forEach((callbacks, eventName) => {
      callbacks.forEach((cb) => {
        socket.off(eventName, cb);
        socket.on(eventName, cb);
      });
    });

    socket.off('connect');
    socket.on('connect', () => setStatus('connected'));

    socket.off('disconnect');
    socket.on('disconnect', () => setStatus('disconnected'));

    socket.off('connect_error');
    socket.on('connect_error', (err) => {
      debug('connect_error', err?.message);
      setStatus('degraded');
      fallbackToSSE();
    });
  };

  const fallbackToSSE = () => {
    if (sseStarted) return;
    sseStarted = true;
    if (eventSource) eventSource.close();
    eventSource = new EventSource('/realtime/stream');
    setStatus('sse');

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
    eventSource.onerror = () => setStatus('disconnected');
  };

  const init = (options = {}) => {
    diagnostics = Boolean(options.diagnostics);
    if (initialized) {
      debug('init_skipped_existing_instance');
      return;
    }
    initialized = true;

    if (window.io) {
      socket = window.io({ transports: ['websocket'], reconnection: true, reconnectionAttempts: Infinity });
      bindSocketEvents();
      return;
    }
    fallbackToSSE();
  };

  const emitCommand = async (eventName, payload = {}) => {
    debug('emit_command', eventName, payload);
    if (socket && socket.connected) {
      return await new Promise((resolve) => {
        socket.timeout(1500).emit(eventName, payload, (err, response) => {
          if (err) {
            debug('socket_ack_error', eventName, err);
            resolve({ status: 'error', reason: 'socket_ack_timeout' });
            return;
          }
          resolve(response || { status: 'ok' });
        });
      });
    }
    const routeMap = {
      start_live: '/realtime/command/start',
      pause_live: '/realtime/command/pause',
      resume_live: '/realtime/command/resume',
      end_live: '/realtime/command/end',
      reset_live: '/realtime/command/reset',
    };
    if (!routeMap[eventName]) {
      return { status: 'error', reason: 'unsupported_command' };
    }
    const resp = await fetch(routeMap[eventName], { method: 'POST' });
    return await resp.json();
  };

  const on = (eventName, callback) => {
    const callbacks = listeners.get(eventName) || [];
    if (!callbacks.includes(callback)) {
      callbacks.push(callback);
      listeners.set(eventName, callbacks);
      if (socket) {
        socket.off(eventName, callback);
        socket.on(eventName, callback);
      }
    }
  };

  const off = (eventName, callback) => {
    const callbacks = listeners.get(eventName) || [];
    listeners.set(eventName, callbacks.filter((cb) => cb !== callback));
    if (socket) socket.off(eventName, callback);
  };

  const destroy = () => {
    listeners.clear();
    initialized = false;
    sseStarted = false;
    diagnostics = false;
    if (socket) {
      socket.removeAllListeners();
      socket.disconnect();
      socket = null;
    }
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  };

  const stats = () => ({
    initialized,
    connected: Boolean(socket && socket.connected),
    listenerEvents: [...listeners.keys()].length,
  });

  return { init, on, off, destroy, emitCommand, stats };
})();
