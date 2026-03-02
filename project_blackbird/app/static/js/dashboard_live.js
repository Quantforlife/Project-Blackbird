(function () {
  const terminal = document.getElementById('terminal');
  const batteryEl = document.getElementById('m-battery');
  const defectsEl = document.getElementById('m-defects');
  const imagesEl = document.getElementById('m-images');
  const flightTimeEl = document.getElementById('m-flight-time');
  const progressEl = document.getElementById('m-progress');
  const progressLabelEl = document.getElementById('m-progress-label');

  const map = L.map('liveMap').setView([37.7749, -122.4194], 14);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

  const droneIcon = L.circleMarker([37.7749, -122.4194], {
    radius: 9,
    color: '#00e5ff',
    fillColor: '#00e5ff',
    fillOpacity: 0.7,
  }).addTo(map);

  const defectLayer = L.layerGroup().addTo(map);
  let lastLogLine = '';

  function updateTerminal(logs) {
    if (!logs || logs.length === 0) {
      return;
    }
    const latest = logs[logs.length - 1];
    if (latest === lastLogLine) {
      return;
    }
    lastLogLine = latest;
    terminal.textContent += latest + '\n';
    terminal.scrollTop = terminal.scrollHeight;
  }

  function renderDefects(defects) {
    defectLayer.clearLayers();
    defects.forEach((marker) => {
      L.circle([marker.lat, marker.lon], {
        radius: 12,
        color: '#ff4d6d',
      }).bindPopup(`Defect: ${marker.type}`).addTo(defectLayer);
    });
  }

  function applyPayload(payload) {
    const telemetry = payload.telemetry;
    batteryEl.textContent = `${telemetry.battery}%`;
    defectsEl.textContent = `${telemetry.active_defects}`;
    imagesEl.textContent = `${telemetry.images_captured}`;
    flightTimeEl.textContent = `${telemetry.flight_time}s`;
    progressEl.style.width = `${telemetry.mission_progress}%`;
    progressLabelEl.textContent = `${telemetry.mission_progress}%`;

    droneIcon.setLatLng([telemetry.latitude, telemetry.longitude]);
    map.panTo([telemetry.latitude, telemetry.longitude], { animate: true, duration: 0.5 });

    renderDefects(payload.defects || []);
    updateTerminal(payload.logs || []);
  }

  const source = new EventSource('/realtime/stream');
  source.addEventListener('telemetry', (event) => {
    const payload = JSON.parse(event.data);
    applyPayload(payload);
  });
})();
