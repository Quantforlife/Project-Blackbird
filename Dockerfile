import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { generateReport, listReports, getReportDownloadUrl } from '../utils/api';

export default function Reports() {
  const { missions, addEvent } = useStore();
  const [reports, setReports]   = useState<any[]>([]);
  const [generating, setGen]    = useState<string|null>(null);
  const [loading, setLoading]   = useState(true);

  const load = async () => {
    try { setReports(await listReports()); } catch {}
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const gen = async (missionId: string, name: string) => {
    setGen(missionId);
    try {
      await generateReport(missionId);
      addEvent('report', `Report queued for "${name}"`, 'info');
      setTimeout(load, 3000);
    } catch { addEvent('report', 'Report generation failed', 'error'); }
    finally { setGen(null); }
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
      <div className="page-grid-3">
        <div className="stat-card"><div className="stat-val">{reports.length}</div><div className="stat-label">Generated Reports</div></div>
        <div className="stat-card"><div className="stat-val" style={{ color:'var(--cyan)' }}>{missions.filter(m=>m.status==='completed').length}</div><div className="stat-label">Completed Missions</div></div>
        <div className="stat-card green"><div className="stat-val text-green">{missions.length}</div><div className="stat-label">Total Missions</div></div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14 }}>
        <div className="card">
          <div className="card-title">Generate Report</div>
          {missions.map(m => (
            <div key={m.id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'9px 0', borderBottom:'1px solid rgba(20,50,69,0.4)' }}>
              <div>
                <div style={{ fontWeight:600, fontSize:13 }}>{m.name}</div>
                <div style={{ fontSize:9, color:'var(--text-lo)', marginTop:2, letterSpacing:1 }}>
                  {m.site_name} · {m.waypoints.length} WPs · {new Date(m.created_at).toLocaleDateString()}
                </div>
              </div>
              <div style={{ display:'flex', gap:6, alignItems:'center' }}>
                <span className={`badge badge-${m.status}`}>{m.status}</span>
                <button className="btn btn-outline btn-sm" onClick={() => gen(m.id, m.name)} disabled={generating===m.id}>
                  {generating===m.id ? '…' : '⬡ PDF'}
                </button>
                <a href={getReportDownloadUrl(m.id)} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">↓</a>
              </div>
            </div>
          ))}
          {missions.length === 0 && <div style={{ fontSize:10, color:'var(--text-lo)', letterSpacing:2 }}>NO MISSIONS</div>}
        </div>

        <div className="card">
          <div className="card-title">Report Archive</div>
          {loading ? (
            <div className="loader" style={{ height:80 }}>LOADING…</div>
          ) : reports.length === 0 ? (
            <div style={{ fontSize:10, color:'var(--text-lo)', letterSpacing:2 }}>NO REPORTS GENERATED</div>
          ) : (
            <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
              {reports.map((r, i) => (
                <div key={i} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'8px 10px', background:'var(--hull)', clipPath:'var(--clip-sm)', border:'1px solid var(--seam)' }}>
                  <div>
                    <div className="mono" style={{ fontSize:10, color:'var(--amber)' }}>{r.filename}</div>
                    <div style={{ fontSize:9, color:'var(--text-lo)', marginTop:2 }}>{r.size_kb} KB · {new Date(r.created_at*1000).toLocaleString()}</div>
                  </div>
                  <a href={`${process.env.REACT_APP_API_URL||'http://localhost:8000'}/uploads/reports/${r.filename}`}
                    target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">↓ DL</a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
