window.BlackbirdVideo = (() => {
  let canvas;
  let ctx;

  const init = () => {
    canvas = document.getElementById('video-canvas');
    ctx = canvas.getContext('2d');
  };

  const drawBackground = (frameId, status) => {
    ctx.fillStyle = '#0B0F14';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#1F2937';
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    ctx.fillStyle = '#E5E7EB';
    ctx.font = '12px Inter';
    ctx.fillText(`FRAME ${String(frameId).padStart(5, '0')} | STATUS ${status.toUpperCase()}`, 12, 18);
  };

  const drawBoxes = (boxes) => {
    boxes.forEach((box) => {
      let color = '#00E5FF';
      if (box.severity === 'critical') color = '#FF3B3B';
      if (box.severity === 'warning') color = '#FFB020';

      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(box.x, box.y, box.w, box.h);

      ctx.fillStyle = color;
      ctx.font = '12px Inter';
      ctx.fillText(`${box.type} ${box.confidence}%`, box.x, Math.max(14, box.y - 6));
    });
  };

  const update = (payload) => {
    const video = payload.video;
    drawBackground(video.frame_id, video.status);
    drawBoxes(video.boxes || []);
  };

  return { init, update };
})();
