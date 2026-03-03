window.BlackbirdVideoOverlay = (() => {
  let canvas;
  let ctx;

  const colorByType = {
    hotspot: '#FF3B3B',
    crack: '#FFB020',
    soiling: '#00E5FF',
  };

  const init = () => {
    canvas = document.getElementById('video-canvas');
    ctx = canvas.getContext('2d');
  };

  const drawBackground = (frameId, pose) => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#0B0F14';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#1F2937';
    for (let x = 0; x < canvas.width; x += 48) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 48) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    ctx.fillStyle = '#E5E7EB';
    ctx.font = '12px Inter';
    ctx.fillText(`FRAME ${String(frameId || 0).padStart(5, '0')}`, 12, 20);
    if (pose) {
      ctx.fillText(`ALT ${Number(pose.altitude || 0).toFixed(1)}m`, 150, 20);
    }
  };

  const normalizeDetection = (item) => {
    if (item.bounding_box) {
      return {
        panel_id: item.panel_id,
        defect_type: item.defect_type,
        confidence: item.confidence,
        box: item.bounding_box,
      };
    }
    if (item.x !== undefined) {
      return {
        panel_id: item.panel_id || 'panel',
        defect_type: item.defect_type || item.type || 'defect',
        confidence: item.confidence || 0.7,
        box: { x: item.x, y: item.y, w: item.w || 44, h: item.h || 36 },
      };
    }
    return null;
  };

  const drawDetections = (detections) => {
    detections.map(normalizeDetection).filter(Boolean).forEach((det) => {
      const color = colorByType[(det.defect_type || '').toLowerCase()] || '#00E5FF';
      const b = det.box;
      ctx.save();
      ctx.globalAlpha = 0.2;
      ctx.fillStyle = color;
      ctx.fillRect(b.x, b.y, b.w, b.h);
      ctx.restore();

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(b.x, b.y, b.w, b.h);

      ctx.fillStyle = color;
      ctx.font = '11px Inter';
      const confidence = Number(det.confidence || 0) * (det.confidence <= 1 ? 100 : 1);
      ctx.fillText(`${det.panel_id} ${det.defect_type} ${confidence.toFixed(1)}%`, b.x, Math.max(12, b.y - 6));
    });
  };

  const updateFrame = (payload) => {
    drawBackground(payload.frame_id, payload.drone_pose);
    drawDetections(payload.detections || []);
  };

  return { init, updateFrame };
})();
