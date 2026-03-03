window.BlackbirdMap = (() => {
  let map;
  let droneMarker;
  let pathLine;
  const defectLayer = L.layerGroup();
  const flashLayer = L.layerGroup();

  const init = () => {
    map = L.map('liveMap', { zoomControl: true }).setView([37.7749, -122.4194], 17);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 21 }).addTo(map);
    L.control.scale({ metric: true, imperial: false }).addTo(map);

    droneMarker = L.circleMarker([37.7749, -122.4194], {
      radius: 8,
      color: '#00E5FF',
      fillColor: '#00E5FF',
      fillOpacity: 0.8,
    }).addTo(map);

    pathLine = L.polyline([], { color: '#00E5FF', weight: 2 }).addTo(map);
    defectLayer.addTo(map);
    flashLayer.addTo(map);

    const mapPane = map.getPanes().overlayPane;
    const grid = document.createElement('div');
    grid.className = 'map-grid';
    mapPane.appendChild(grid);
  };

  const update = (payload) => {
    const telemetry = payload.telemetry;
    const defects = payload.defects || [];

    droneMarker.setLatLng([telemetry.latitude, telemetry.longitude]);
    document.getElementById('coord-readout').textContent =
      `Lat ${telemetry.latitude.toFixed(6)}, Lon ${telemetry.longitude.toFixed(6)}`;

    const path = (payload.path || []).slice(0, telemetry.images_captured + 1)
      .map((p) => [p.lat, p.lon]);
    pathLine.setLatLngs(path);

    if (telemetry.mode === 'live') {
      map.panTo([telemetry.latitude, telemetry.longitude], { animate: true, duration: 0.45 });
    }

    defectLayer.clearLayers();
    defects.forEach((d) => {
      const color = d.severity === 'critical' ? '#FF3B3B' : (d.severity === 'warning' ? '#FFB020' : '#00E5FF');
      L.circleMarker([d.lat, d.lon], { radius: 6, color }).addTo(defectLayer)
        .bindPopup(`${d.type} (${d.confidence}%)`);
    });

    const latest = defects[defects.length - 1];
    if (latest && latest.id === payload.analytics.total) {
      flashLayer.clearLayers();
      const flash = L.circle([latest.lat, latest.lon], { radius: 20, color: '#00FFA3' }).addTo(flashLayer);
      setTimeout(() => flash.remove(), 700);
    }
  };

  return { init, update };
})();
