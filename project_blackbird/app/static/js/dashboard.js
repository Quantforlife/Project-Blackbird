(() => {
  const state = {
    detections: new Map(),
    lastWaypoint: null,
    initialized: false,
    missionState: 'idle',
    playbackMode: false,
  };

  const kpi = {
    battery: document.getElementById('kpi-battery'),
    progress: document.getElementById('kpi-progress'),
    flightTime: document.getElementById('kpi-flight-time'),
    defects: document.getElementById('kpi-defects'),
    waypoint: document.getElementById('kpi-waypoint'),
  };

  const updateKpi = (el, value) => {
    if (!el || el.textContent === value) return;
    el.textContent = value;
    const card = el.closest('.kpi-card');
    if (card) {
      card.classList.add('kpi-updated');
      setTimeout(() => card.classList.remove('kpi-updated'), 260);
    }
  };

  const renderDetectionsTable = () => {
    const tbody = document.querySelector('#detections-table tbody');
    tbody.innerHTML = '';
    [...state.detections.values()].slice(-20).reverse().forEach((d) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${d.panel_id}</td><td>${d.defect_type}</td>
        <td>${(Number(d.average_confidence || d.confidence || 0) * 100).toFixed(1)}%</td>
        <td>${d.severity || '-'}</td>
        <td>${Number(d.geo_location?.latitude || 0).toFixed(6)}</td>
        <td>${Number(d.geo_location?.longitude || 0).toFixed(6)}</td>`;
      tbody.appendChild(tr);
    });
    updateKpi(kpi.defects, String(state.detections.size));
  };

  const updateCommandAvailability = () => {
    const buttons = {
      start: document.querySelector('[data-live-command="start"]'),
      pause: document.querySelector('[data-live-command="pause"]'),
      resume: document.querySelector('[data-live-command="resume"]'),
      end: document.querySelector('[data-live-command="end"]'),
      reset: document.querySelector('[data-live-command="reset"]'),
    };
    const running = state.missionState === 'running';
    const paused = state.missionState === 'paused';
    buttons.start.disabled = running;
    buttons.pause.disabled = !running;
    buttons.resume.disabled = !paused;
    buttons.end.disabled = !running && !paused;
    buttons.reset.disabled = running;
  };

  const setConnectionStatus = ({ status }) => {
    const node = document.getElementById('connection-status');
    if (!node) return;
    node.textContent = status.toUpperCase();
    node.dataset.status = status;
  };

  let lastTelemetryFrame = 0;
  const onTelemetry = (payload) => {
    const now = performance.now();
    if (now - lastTelemetryFrame < 80) return;
    lastTelemetryFrame = now;

    BlackbirdMapRenderer.updateTelemetry(payload);
    updateKpi(kpi.battery, `${Math.round(payload.battery || 0)}%`);
    updateKpi(kpi.progress, `${Math.round(payload.mission_progress || 0)}%`);
    updateKpi(kpi.flightTime, `${Number(payload.timestamp || 0).toFixed(1)}s`);
    updateKpi(kpi.waypoint, `${payload.waypoint_index ?? 0}`);

    BlackbirdMissionControls.updateTimeline(Number(payload.timestamp || 0), 180);

    if (state.lastWaypoint !== payload.waypoint_index) {
      state.lastWaypoint = payload.waypoint_index;
      BlackbirdTerminalConsole.pushEvent({ timestamp: payload.timestamp, type: 'GPS', message: `Transitioned to waypoint ${payload.waypoint_index}` });
    }
  };

  const onFrame = (payload) => BlackbirdVideoOverlay.updateFrame(payload);

  const onDetection = (payload) => {
    const d = payload.detection || {};
    state.detections.set(`${d.panel_id}:${d.defect_type}`, d);
    renderDetectionsTable();
    BlackbirdMapRenderer.updateDefect(payload);
  };

  const onMissionComplete = (payload) => {
    state.missionState = 'completed';
    updateCommandAvailability();
    BlackbirdTerminalConsole.pushEvent({ timestamp: payload.timestamp, type: 'SYSTEM', message: 'Mission complete — all waypoints scanned' });
  };

  const events = {
    telemetry_update: onTelemetry,
    frame_update: onFrame,
    detection_confirmed: onDetection,
    mission_progress: BlackbirdMapRenderer.updateProgress,
    terminal_event: BlackbirdTerminalConsole.pushEvent,
    mission_complete: onMissionComplete,
    connection_status: setConnectionStatus,
  };

  const bindSocketEvents = () => Object.entries(events).forEach(([n, h]) => BlackbirdSocketClient.on(n, h));
  const unbindSocketEvents = () => Object.entries(events).forEach(([n, h]) => BlackbirdSocketClient.off(n, h));

  const syncControllerState = (controllerState = {}) => {
    state.playbackMode = Boolean(controllerState.playback_mode);
    if (controllerState.running && !controllerState.paused) state.missionState = 'running';
    if (controllerState.running && controllerState.paused) state.missionState = 'paused';
    if (!controllerState.running && state.missionState !== 'completed') state.missionState = 'idle';
    updateCommandAvailability();
  };

  const commandHandlers = {
    onCommand: async (action) => {
      const response = await fetch(`/realtime/command/${action}`, { method: 'POST' });
      const payload = await response.json();
      syncControllerState(payload.controller || {});
      const labels = { start: 'Mission start', pause: 'Mission paused', resume: 'Mission resumed', end: 'Mission ended', reset: 'Mission reset' };
      BlackbirdTerminalConsole.pushEvent({ timestamp: performance.now() / 1000, type: 'SYSTEM', message: labels[action] || action });
      if (action === 'reset') {
        state.detections.clear();
        renderDetectionsTable();
        BlackbirdTerminalConsole.clear();
      }
    },
    onMode: async (mode) => {
      const response = await fetch(`/realtime/mode/${mode}`, { method: 'POST' });
      const payload = await response.json();
      syncControllerState(payload.controller || {});
      BlackbirdMissionControls.setPlaybackMode(mode === 'playback');
      BlackbirdTerminalConsole.pushEvent({ timestamp: performance.now() / 1000, type: 'SYSTEM', message: `${mode.toUpperCase()} mode enabled` });
    },
    onSeek: async (timestamp) => {
      const step = Math.max(0, Math.floor(timestamp));
      await fetch(`/realtime/playback/${step}`, { method: 'POST' });
    },
  };

  const bindFilterControls = () => {
    const tileMode = document.getElementById('map-tile-mode');
    const togglePath = document.getElementById('toggle-path');
    const defectToggles = () => Array.from(document.querySelectorAll('.defect-toggle')).filter((el) => el.checked).map((el) => el.value);
    const flightFilter = document.getElementById('flight-status-filter');

    const apply = () => {
      BlackbirdMapRenderer.setFilters({
        tile: tileMode.value,
        showPath: togglePath.checked,
        visibleDefects: new Set(defectToggles()),
        flightFilter: flightFilter.value,
      });
    };

    [tileMode, togglePath, flightFilter].forEach((el) => el.addEventListener('change', apply));
    document.querySelectorAll('.defect-toggle').forEach((el) => el.addEventListener('change', apply));
    apply();
  };

  const teardown = () => {
    unbindSocketEvents();
    BlackbirdMissionControls.teardown();
    BlackbirdSocketClient.destroy();
    BlackbirdMapRenderer.teardown();
  };

  const init = () => {
    if (state.initialized) return;
    state.initialized = true;

    BlackbirdMapRenderer.init();
    BlackbirdVideoOverlay.init();
    BlackbirdTerminalConsole.init();

    BlackbirdMissionControls.bind(commandHandlers);
    bindFilterControls();
    updateCommandAvailability();

    BlackbirdSocketClient.init();
    bindSocketEvents();

    window.addEventListener('beforeunload', teardown, { once: true });
  };

  window.addEventListener('DOMContentLoaded', init, { once: true });
})();
