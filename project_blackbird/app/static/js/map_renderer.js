window.BlackbirdMapRenderer = (() => {
  let map;
  let droneMarker;
  let missionPath;
  let activePanel;
  const defectLayer = L.layerGroup();
  const scannedLayer = L.layerGroup();
  const defectMarkers = [];
  let lastPoint = null;
  let animationFrame = null;
  let destroyed = false;
  let mapState = { tile: 'satellite', showPath: true, visibleDefects: new Set(['hotspot', 'crack', 'soiling']), flightFilter: 'all' };

  const OSM_TILE = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  const SAT_TILE = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
  const labelsTile = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  let satelliteLayer;
  let streetLayer;
  let hybridLabels;

  const applyTileMode = (mode) => {
    mapState.tile = mode;
    [satelliteLayer, streetLayer, hybridLabels].forEach((layer) => {
      if (layer && map.hasLayer(layer)) {
        map.removeLayer(layer);
      }
    });
    if (mode === 'street') {
      streetLayer.addTo(map);
      return;
    }
    if (mode === 'hybrid') {
      satelliteLayer.addTo(map);
      hybridLabels.addTo(map);
      return;
    }
    satelliteLayer.addTo(map);
  };

  const init = () => {
    destroyed = false;
    map = L.map('liveMap', { zoomControl: true, minZoom: 16, maxZoom: 21, preferCanvas: true }).setView([37.7749, -122.4194], 18);

    streetLayer = L.tileLayer(OSM_TILE, { maxZoom: 21, attribution: '&copy; OpenStreetMap contributors' });
    satelliteLayer = L.tileLayer(SAT_TILE, {
      maxZoom: 21,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics',
    });
    hybridLabels = L.tileLayer(labelsTile, { maxZoom: 21, opacity: 0.25, attribution: '&copy; OpenStreetMap contributors' });

    satelliteLayer.on('tileerror', () => {
      if (!map.hasLayer(streetLayer)) {
        streetLayer.addTo(map);
      }
    });

    applyTileMode('satellite');
    L.control.scale({ metric: true, imperial: false }).addTo(map);

    missionPath = L.polyline([], { color: '#00c853', weight: 2, opacity: 0.8 }).addTo(map);
    droneMarker = L.circleMarker([37.7749, -122.4194], { radius: 7, color: '#00c853', fillColor: '#00c853', fillOpacity: 0.9 }).addTo(map);
    activePanel = L.circleMarker([37.7749, -122.4194], { radius: 10, color: '#00a846', fillColor: '#00a846', fillOpacity: 0.15, weight: 2 }).addTo(map);

    defectLayer.addTo(map);
    scannedLayer.addTo(map);
  };

  const smoothPosition = (toLatLng) => {
    if (destroyed || !droneMarker) return;
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
      droneMarker.setLatLng([
        from[0] + ((toLatLng[0] - from[0]) * progress),
        from[1] + ((toLatLng[1] - from[1]) * progress),
      ]);
      if (progress < 1 && !destroyed) {
        animationFrame = requestAnimationFrame(animate);
      }
    };
    animationFrame = requestAnimationFrame(animate);
    lastPoint = toLatLng;
  };

  const refreshDefects = () => {
    defectLayer.clearLayers();
    const defectsAllowed = mapState.flightFilter !== 'with_defects' || defectMarkers.length > 0;
    if (!defectsAllowed) {
      return;
    }
    defectMarkers.forEach((entry) => {
      if (!mapState.visibleDefects.has(entry.kind)) {
        return;
      }
      entry.marker.addTo(defectLayer);
    });
  };

  const updateTelemetry = (payload) => {
    if (destroyed || !map) return;
    const pos = [payload.latitude || 0, payload.longitude || 0];
    smoothPosition(pos);

    const points = missionPath.getLatLngs();
    points.push(pos);
    missionPath.setLatLngs(points.slice(-500));

    scannedLayer.clearLayers();
    if (mapState.showPath) {
      points.slice(-20).forEach((pt) => L.circleMarker(pt, { radius: 3, color: '#1f2321', fillColor: '#00c853', fillOpacity: 0.35 }).addTo(scannedLayer));
      if (!map.hasLayer(missionPath)) missionPath.addTo(map);
    } else if (map.hasLayer(missionPath)) {
      map.removeLayer(missionPath);
    }

    activePanel.setLatLng(pos);
    map.panTo(pos, { animate: true, duration: 0.35 });
    document.getElementById('latlon-readout').textContent = `Lat ${Number(pos[0]).toFixed(6)}, Lon ${Number(pos[1]).toFixed(6)}`;
    document.getElementById('map-progress-label').textContent = `${Math.round(payload.mission_progress || 0)}%`;
  };

  const updateProgress = (payload) => {
    const node = document.getElementById('map-progress-label');
    if (node) node.textContent = `${Math.round(payload.mission_progress || 0)}%`;
  };

  const updateDefect = (payload) => {
    const d = payload.detection || {};
    const geo = d.geo_location || {};
    const kind = String(d.defect_type || 'unknown').toLowerCase();
    const color = kind === 'hotspot' ? '#d50000' : '#00c853';
    const marker = L.circleMarker([geo.latitude, geo.longitude], {
      radius: 6,
      color,
      fillColor: color,
      fillOpacity: 0.85,
      className: 'pulse-marker',
    });
    marker.bindPopup(`${d.panel_id} ${d.defect_type}`);
    defectMarkers.push({ kind, marker });
    refreshDefects();
  };

  const setFilters = (filters) => {
    mapState = {
      ...mapState,
      ...filters,
      visibleDefects: filters.visibleDefects || mapState.visibleDefects,
    };
    if (map) applyTileMode(mapState.tile);
    refreshDefects();
  };

  const teardown = () => {
    destroyed = true;
    if (animationFrame) cancelAnimationFrame(animationFrame);
    defectMarkers.length = 0;
    if (map) {
      map.remove();
      map = null;
    }
  };

  return { init, updateTelemetry, updateProgress, updateDefect, setFilters, teardown };
})();
