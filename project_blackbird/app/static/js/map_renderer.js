window.BlackbirdMapRenderer = (() => {
  let map;
  let droneMarker;
  let missionPath;
  let activePanel;
  const defectLayer = L.layerGroup();
  const scannedLayer = L.layerGroup();
  let lastPoint = null;
  let animationFrame = null;
  let destroyed = false;

  const OSM_TILE = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  const SAT_TILE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

  const init = () => {
    destroyed = false;
    map = L.map('liveMap', { zoomControl: true, minZoom: 16, maxZoom: 21 }).setView([37.7749, -122.4194], 18);
    const fallback = L.tileLayer(OSM_TILE, {
      maxZoom: 21,
      attribution: '&copy; OpenStreetMap contributors',
    });
    const satellite = L.tileLayer(SAT_TILE, {
      maxZoom: 21,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics',
    });
    satellite.on('tileerror', () => {
      if (!map.hasLayer(fallback)) {
        fallback.addTo(map);
      }
    });
    satellite.addTo(map);

    L.control.scale({ metric: true, imperial: false }).addTo(map);

    missionPath = L.polyline([], { color: '#00E5FF', weight: 2, opacity: 0.8 }).addTo(map);
    droneMarker = L.circleMarker([37.7749, -122.4194], {
      radius: 7,
      color: '#00E5FF',
      fillColor: '#00E5FF',
      fillOpacity: 0.9,
    }).addTo(map);
    activePanel = L.circleMarker([37.7749, -122.4194], {
      radius: 10,
      color: '#00FFA3',
      fillColor: '#00FFA3',
      fillOpacity: 0.15,
      weight: 2,
    }).addTo(map);

    defectLayer.addTo(map);
    scannedLayer.addTo(map);
  };

  const smoothPosition = (toLatLng) => {
    if (destroyed || !droneMarker) {
      return;
    }
    if (!lastPoint) {
      lastPoint = toLatLng;
      droneMarker.setLatLng(toLatLng);
      return;
    }

    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }

    const from = [...lastPoint];
    const start = performance.now();
    const duration = 250;
    const animate = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const lat = from[0] + ((toLatLng[0] - from[0]) * progress);
      const lon = from[1] + ((toLatLng[1] - from[1]) * progress);
      droneMarker.setLatLng([lat, lon]);
      if (progress < 1 && !destroyed) {
        animationFrame = requestAnimationFrame(animate);
      }
    };
    animationFrame = requestAnimationFrame(animate);
    lastPoint = toLatLng;
  };

  const updateTelemetry = (payload) => {
    if (destroyed || !map) {
      return;
    }
    const pos = [payload.latitude || 0, payload.longitude || 0];
    smoothPosition(pos);

    const points = missionPath.getLatLngs();
    points.push(pos);
    missionPath.setLatLngs(points.slice(-500));

    scannedLayer.clearLayers();
    points.slice(-20).forEach((pt) => {
      L.circleMarker(pt, { radius: 3, color: '#1F2937', fillColor: '#00E5FF', fillOpacity: 0.35 }).addTo(scannedLayer);
    });

    activePanel.setLatLng(pos);
    map.panTo(pos, { animate: true, duration: 0.35 });
    document.getElementById('latlon-readout').textContent =
      `Lat ${Number(pos[0]).toFixed(6)}, Lon ${Number(pos[1]).toFixed(6)}`;
    document.getElementById('map-progress-label').textContent = `${Math.round(payload.mission_progress || 0)}%`;
  };

  const updateProgress = (payload) => {
    const value = Math.round(payload.mission_progress || 0);
    const node = document.getElementById('map-progress-label');
    if (node) {
      node.textContent = `${value}%`;
    }
  };

  const updateDefect = (payload) => {
    const d = payload.detection || {};
    const geo = d.geo_location || {};
    const defectType = (d.defect_type || '').toLowerCase();
    const color = defectType === 'hotspot' ? '#FF3B3B' : (defectType === 'crack' ? '#FFB020' : '#00E5FF');
    const marker = L.circleMarker([geo.latitude, geo.longitude], {
      radius: 6,
      color,
      fillColor: color,
      fillOpacity: 0.85,
      className: 'pulse-marker',
    }).addTo(defectLayer);
    marker.bindPopup(`${d.panel_id} ${d.defect_type}`);
  };

  const teardown = () => {
    destroyed = true;
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
      animationFrame = null;
    }
    if (map) {
      map.remove();
      map = null;
    }
  };

  return { init, updateTelemetry, updateProgress, updateDefect, teardown };
})();
