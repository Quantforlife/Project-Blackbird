import React, { useRef, useState, useEffect, useCallback } from 'react';
import { useStore } from '../store';
import { getMissionImages, getImageUrl, createDetection, deleteDetection, getImageDetections } from '../utils/api';
import type { DroneImage, Detection } from '../types';

const LABELS = ['soiling','hot_spot','crack','delamination','micro_crack','corrosion','glass_breakage','bypass_diode_failure','shading','physical_damage'];
const SEV_MAP: Record<string, string> = { soiling:'low', shading:'low', micro_crack:'medium', hot_spot:'medium', crack:'high', delamination:'high', corrosion:'high', bypass_diode_failure:'critical', glass_breakage:'critical', physical_damage:'critical' };
const SEV_COLOR: Record<string, string> = { low:'var(--green)', medium:'var(--yellow)', high:'var(--amber)', critical:'var(--red)' };

interface BBox { x:number; y:number; w:number; h:number }

export default function AnnotationTool() {
  const { missions } = useStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef    = useRef<HTMLImageElement>(null);
  const [missionId, setMissionId] = useState('');
  const [images, setImages]       = useState<DroneImage[]>([]);
  const [idx, setIdx]             = useState(0);
  const [detections, setDets]     = useState<Detection[]>([]);
  const [label, setLabel]         = useState(LABELS[0]);
  const [drawing, setDrawing]     = useState(false);
  const [startPt, setStart]       = useState<{x:number;y:number}|null>(null);
  const [box, setBox]             = useState<BBox|null>(null);

  const cur = images[idx] || null;

  useEffect(() => {
    if (!missionId) return;
    getMissionImages(missionId).then(setImages);
  }, [missionId]);

  useEffect(() => {
    if (!cur) return;
    getImageDetections(cur.id).then(setDets);
  }, [cur?.id]);

  const redraw = useCallback(() => {
    const cv = canvasRef.current, im = imgRef.current;
    if (!cv || !im) return;
    const ctx = cv.getContext('2d')!;
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.drawImage(im, 0, 0, cv.width, cv.height);
    detections.forEach(d => {
      const x=d.bbox_x*cv.width, y=d.bbox_y*cv.height, w=d.bbox_w*cv.width, h=d.bbox_h*cv.height;
      const c = SEV_COLOR[d.severity] || 'var(--cyan)';
      ctx.strokeStyle = c.replace('var(--','').replace(')','') === 'amber' ? '#e8860a' : c.includes('green') ? '#00e05a' : c.includes('red') ? '#e02040' : c.includes('yellow') ? '#e0c000' : '#00c8e0';
      ctx.strokeStyle = c;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = ctx.strokeStyle + '22';
      ctx.fillRect(x, y, w, h);
      ctx.fillStyle = ctx.strokeStyle;
      ctx.font = 'bold 9px Share Tech Mono,monospace';
      ctx.fillText(`${d.label} ${(d.confidence*100).toFixed(0)}%`, x+2, y+11);
    });
    if (box) {
      ctx.strokeStyle = '#e8860a'; ctx.lineWidth = 2;
      ctx.setLineDash([4,3]); ctx.strokeRect(box.x, box.y, box.w, box.h); ctx.setLineDash([]);
    }
  }, [detections, box]);

  useEffect(() => { redraw(); }, [redraw]);

  const xy = (e: React.MouseEvent) => {
    const cv = canvasRef.current!; const r = cv.getBoundingClientRect();
    return { x:(e.clientX-r.left)*(cv.width/r.width), y:(e.clientY-r.top)*(cv.height/r.height) };
  };

  const onDown = (e: React.MouseEvent) => { setDrawing(true); setStart(xy(e)); setBox(null); };
  const onMove = (e: React.MouseEvent) => {
    if (!drawing || !startPt) return;
    const p = xy(e);
    setBox({ x:Math.min(startPt.x,p.x), y:Math.min(startPt.y,p.y), w:Math.abs(p.x-startPt.x), h:Math.abs(p.y-startPt.y) });
  };
  const onUp = async () => {
    if (!drawing || !box || !cur) return;
    setDrawing(false);
    const cv = canvasRef.current!;
    if (box.w < 6 || box.h < 6) { setBox(null); return; }
    try {
      const det = await createDetection({ image_id:cur.id, label, confidence:1.0, severity:SEV_MAP[label]||'low', bbox_x:box.x/cv.width, bbox_y:box.y/cv.height, bbox_w:box.w/cv.width, bbox_h:box.h/cv.height, is_manual:true });
      setDets(prev => [...prev, det]);
    } catch {}
    setBox(null);
  };

  return (
    <div style={{ display:'grid', gridTemplateColumns:'1fr 260px', gap:12, height:'calc(100vh - 94px)' }}>
      <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
        <div className="card" style={{ padding:'8px 12px', display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
          <select value={missionId} onChange={e => { setMissionId(e.target.value); setIdx(0); }} style={{ flex:1 }}>
            <option value="">Select mission…</option>
            {missions.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
          {images.length > 0 && (
            <>
              <button className="btn btn-ghost btn-sm" onClick={() => setIdx(i=>Math.max(0,i-1))} disabled={idx===0}>←</button>
              <span className="mono" style={{ fontSize:10, color:'var(--text-mid)' }}>{idx+1}/{images.length}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => setIdx(i=>Math.min(images.length-1,i+1))} disabled={idx===images.length-1}>→</button>
            </>
          )}
          <div style={{ fontSize:9, color:'var(--text-lo)', letterSpacing:1 }}>DRAG TO ANNOTATE</div>
        </div>
        <div style={{ flex:1, background:'var(--abyss)', border:'1px solid var(--seam)', clipPath:'var(--clip-md)', overflow:'hidden', position:'relative', cursor:'crosshair' }}>
          {cur ? (
            <>
              <img ref={imgRef} src={getImageUrl(cur.id)} alt="" style={{ display:'none' }} onLoad={redraw} />
              <canvas ref={canvasRef} width={640} height={480} style={{ width:'100%', height:'100%', display:'block' }}
                onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp} />
            </>
          ) : <div className="loader">SELECT MISSION AND IMAGE</div>}
        </div>
      </div>

      <div style={{ display:'flex', flexDirection:'column', gap:10, overflowY:'auto' }}>
        <div className="card">
          <div className="card-title">Defect Label</div>
          <div style={{ display:'flex', flexDirection:'column', gap:3 }}>
            {LABELS.map(l => {
              const sev = SEV_MAP[l] || 'low';
              const col = SEV_COLOR[sev];
              return (
                <button key={l} onClick={() => setLabel(l)} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'6px 8px', background:label===l ? 'var(--amber-dim)' : 'var(--hull)', border:`1px solid ${label===l ? 'rgba(232,134,10,0.4)' : 'transparent'}`, color:label===l ? 'var(--amber)' : 'var(--text-mid)', cursor:'pointer', clipPath:'var(--clip-sm)', fontSize:10, letterSpacing:1 }}>
                  <span>{l.replace(/_/g,' ')}</span>
                  <span style={{ fontSize:8, color:col, letterSpacing:1 }}>{sev}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div className="card" style={{ flex:1 }}>
          <div className="card-title">Annotations ({detections.length})</div>
          <div style={{ display:'flex', flexDirection:'column', gap:5, overflowY:'auto', maxHeight:280 }}>
            {detections.map(d => {
              const c = SEV_COLOR[d.severity];
              return (
                <div key={d.id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'5px 0', borderBottom:'1px solid rgba(20,50,69,0.4)' }}>
                  <div>
                    <div style={{ fontSize:11, fontWeight:600, color:c }}>{d.label.replace(/_/g,' ')}</div>
                    <div style={{ fontSize:8, color:'var(--text-lo)', letterSpacing:1 }}>{d.is_manual?'MANUAL':'AUTO'} · {(d.confidence*100).toFixed(0)}%</div>
                  </div>
                  <button onClick={async () => { await deleteDetection(d.id); setDets(prev=>prev.filter(x=>x.id!==d.id)); }}
                    style={{ background:'none', border:'none', color:'var(--red)', cursor:'pointer', fontSize:16 }}>×</button>
                </div>
              );
            })}
            {detections.length===0 && <div style={{ fontSize:10, color:'var(--text-lo)', letterSpacing:2 }}>NO ANNOTATIONS</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
