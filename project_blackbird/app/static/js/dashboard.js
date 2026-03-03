(() => {
  const state = {
    detections: new Map(),
    lastWaypoint: null,
  };

  const kpi = {
    battery: document.getElementById('kpi-battery'),
    progress: document.getElementById('kpi-progress'),
    flightTime: document.getElementById('kpi-flight-time'),
    defects: document.getElementById('kpi-defects'),
    waypoint: document.getElementById('kpi-waypoint'),
    signal: document.getElementById('kpi-signal'),
  };

  const updateKpi = (el, value) => {
    if (!el || el.textContent === value) {
      return;
    }
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
        <td>${d.panel_id}</td>
        <td>${d.defect_type}</td>
        <td>${(Number(d.average_confidence || d.confidence || 0) * 100).toFixed(1)}%</td>
        <td>${d.severity || '-'}</td>
        <td>${Number(d.geo_location?.latitude || 0).toFixed(6)}</td>
        <td>${Number(d.geo_location?.longitude || 0).toFixed(6)}</td>
      `;
      tbody.appendChild(tr);
    });
    updateKpi(kpi.defects, String(state.detections.size));
  };

  const onTelemetry = (payload) => {
    BlackbirdMapRenderer.updateTelemetry(payload);
    updateKpi(kpi.battery, `${Math.round(payload.battery || 0)}%`);
    updateKpi(kpi.progress, `${Math.round(payload.mission_progress || 0)}%`);
    updateKpi(kpi.flightTime, `${Number(payload.timestamp || 0).toFixed(1)}s`);
    updateKpi(kpi.waypoint, `${payload.waypoint_index ?? 0}`);
    updateKpi(kpi.signal, Number(payload.battery || 0) > 20 ? 'ONLINE' : 'DEGRADED');

    BlackbirdMissionControls.updateTimeline(Number(payload.timestamp || 0), 180);

    if (state.lastWaypoint !== payload.waypoint_index) {
      state.lastWaypoint = payload.waypoint_index;
      BlackbirdTerminalConsole.pushEvent({
        timestamp: payload.timestamp,
        type: 'GPS',
        message: `Transitioned to waypoint ${payload.waypoint_index}`,
      });
    }
  };

  const onFrame = (payload) => {
    BlackbirdVideoOverlay.updateFrame(payload);
  };

  const onDetection = (payload) => {
    const d = payload.detection || {};
    state.detections.set(`${d.panel_id}:${d.defect_type}`, d);
    renderDetectionsTable();
    BlackbirdMapRenderer.updateDefect(payload);
  };

  const onMissionComplete = (payload) => {
    BlackbirdTerminalConsole.pushEvent({
      timestamp: payload.timestamp,
      type: 'SYSTEM',
      message: 'Mission complete — all waypoints scanned',
    });
  };

  const bindSocketEvents = () => {
    BlackbirdSocketClient.on('telemetry_update', onTelemetry);
    BlackbirdSocketClient.on('frame_update', onFrame);
    BlackbirdSocketClient.on('detection_confirmed', onDetection);
    BlackbirdSocketClient.on('mission_progress', BlackbirdMapRenderer.updateProgress);
    BlackbirdSocketClient.on('terminal_event', BlackbirdTerminalConsole.pushEvent);
    BlackbirdSocketClient.on('mission_complete', onMissionComplete);
  };

  const commandHandlers = {
    onCommand: async (action) => {
      await fetch(`/realtime/command/${action}`, { method: 'POST' });
      const labels = { start: 'Mission start', pause: 'Mission paused', resume: 'Mission resumed', end: 'Mission ended' };
      BlackbirdTerminalConsole.pushEvent({ timestamp: performance.now() / 1000, type: 'SYSTEM', message: labels[action] || action });
    },
    onMode: async (mode) => {
      await fetch(`/realtime/mode/${mode}`, { method: 'POST' });
      BlackbirdMissionControls.setPlaybackMode(mode === 'playback');
      BlackbirdTerminalConsole.pushEvent({ timestamp: performance.now() / 1000, type: 'SYSTEM', message: `${mode.toUpperCase()} mode enabled` });
    },
    onSeek: async (timestamp) => {
      const step = Math.max(0, Math.floor(timestamp));
      await fetch(`/realtime/playback/${step}`, { method: 'POST' });
    },
  };

  const bootSequence = (investorMode) => {
    if (!investorMode) {
      return;
    }
    const lines = [
      '[SYS] Initializing Blackbird OS v0.9',
      '[SYS] Loading mission profile',
      '[GPS] RTK lock acquired',
      '[AI] Model loaded — Edge mode',
      '[SYS] Mission start',
    ];
    lines.forEach((line, idx) => {
      setTimeout(() => {
        const type = line.includes('[AI]') ? 'AI' : (line.includes('[GPS]') ? 'GPS' : 'SYSTEM');
        BlackbirdTerminalConsole.pushEvent({ timestamp: idx * 0.2, type, message: line.replace(/^\[[^\]]+\]\s*/, '') });
      }, idx * 120);
    });
    setTimeout(() => {
      commandHandlers.onCommand('start');
    }, 800);
  };

  const init = () => {
    BlackbirdMapRenderer.init();
    BlackbirdVideoOverlay.init();
    BlackbirdTerminalConsole.init();

    BlackbirdMissionControls.bind(commandHandlers);
    BlackbirdSocketClient.init();
    bindSocketEvents();

    const investorMode = document.getElementById('dashboard-root').dataset.investorDemo === '1';
    bootSequence(investorMode);
  };

  window.addEventListener('DOMContentLoaded', init);
})();
