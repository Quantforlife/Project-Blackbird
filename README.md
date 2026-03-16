import React, { useEffect, useState } from 'react';
import { useStore } from '../store';
import { getMissionAnalytics } from '../utils/api';
import type { MissionAnalytics } from '../types';

function BatBar({ pct }: { pct: number }) {
  const c = pct > 60 ? 'var(--green)' : pct > 30 ? 'var(--yellow)' : 'var(--red)';
  return (
    <div className="battery-bar-wrap">
      <div className="battery-bar">
        <div className="battery-fill" style={{ width: `${pct}%`, background: c }} />
      </div>
      <span className="battery-val mono" style={{ color: c }}>{pct.toFixed(0)}%</span>
    </div>
  );
}

function DroneCard({ drone }: { drone: any }) {
  const t = useStore(s => s.telemetry[drone.id]);
  const bat = t?.battery_pct ?? drone.battery_pct;
  const c = ['var(--cyan)', 'var(--amber)', 'var(--green)'];
  const idx = useStore(s => s.drones.findIndex(d => d.id === drone.id));
  const col = c[idx % c.length];

  return (
    <div className="card" style={{ borderLeft: `2px solid ${col}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 14, color: col, letterSpacing: 1 }}>{drone.name}</div>
          <div style={{ fontSize: 9, color: 'var(--text-lo)', letterSpacing: 1, marginTop: 1 }}>{drone.model}</div>
        </div>
        <span className={`badge badge-${drone.status}`}>{drone.status}</span>
      </div>
      <BatBar pct={bat} />
      {t && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4, marginTop: 8 }}>
          {[['ALT', `${t.altitude_m.toFixed(0)}m`], ['SPD', `${t.speed_ms.toFixed(1)}m/s`],
            ['HDG', `${t.heading_deg.toFixed(0)}°`], ['SIG', `${t.signal_dbm.toFixed(0)}dBm`]].map(([k, v]) => (
            <div key={k} className="tac-row" style={{ padding: '3px 0' }}>
              <span className="tac-key">{k}</span>
              <span className="tac-val" style={{ fontSize: 10 }}>{v}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SevBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  return (
    <div className="sev-row">
      <div className="sev-label" style={{ color }}>{label}</div>
      <div className="sev-track">
        <div className="sev-fill" style={{ width: `${total > 0 ? (count / total * 100) : 0}%`, background: color }} />
      </div>
      <div className="sev-count">{count}</div>
    </div>
  );
}

export default function Dashboard() {
  const { drones, missions, assets, events } = useStore();
  const [analytics, setAnalytics] = useState<MissionAnalytics | null>(null);
  const activeMission = missions.find(m => m.status === 'active');

  useEffect(() => {
    if (activeMission) getMissionAnalytics(activeMission.id).then(setAnalytics).catch(() => {});
  }, [activeMission?.id]);

  const flying   = drones.filter(d => d.status === 'flying').length;
  const healthy  = assets.filter(a => a.condition_score >= 80).length;
  const defects  = analytics?.defects_found ?? 0;
  const coverage = analytics?.coverage_pct ?? 0;

  const sevMap = analytics?.defects_by_severity ?? {};
  const sevTotal = Object.values(sevMap).reduce((a, b) => a + b, 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* KPIs */}
      <div className="page-grid-4">
        <div className="stat-card green">
          <div className="stat-val text-green">{flying}</div>
          <div className="stat-label">Airborne</div>
          <div className="stat-sub">{drones.length} total units</div>
        </div>
        <div className="stat-card">
          <div className="stat-val" style={{ color: 'var(--cyan)' }}>{missions.filter(m => m.status === 'active').length}</div>
          <div className="stat-label">Active Missions</div>
          <div className="stat-sub">{missions.length} total</div>
        </div>
        <div className="stat-card red">
          <div className="stat-val text-red">{defects}</div>
          <div className="stat-label">Defects Detected</div>
          <div className="stat-sub">Current mission</div>
        </div>
        <div className="stat-card green">
          <div className="stat-val text-green">{healthy}</div>
          <div className="stat-label">Assets Nominal</div>
          <div className="stat-sub">{assets.length} total assets</div>
        </div>
      </div>

      <div className="page-cols page-cols-2-1">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Active mission banner */}
          {activeMission && (
            <div className="card" style={{ borderColor: 'rgba(232,134,10,0.4)', background: 'var(--amber-dim)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 9, letterSpacing: 3, color: 'var(--amber)', marginBottom: 3 }}>ACTIVE MISSION</div>
                  <div style={{ fontSize: 16, fontWeight: 700, letterSpacing: 1 }}>{activeMission.name}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-mid)', marginTop: 2 }}>{activeMission.site_name}</div>
                </div>
                {analytics && (
                  <div style={{ display: 'flex', gap: 24, textAlign: 'center' }}>
                    {[['Coverage', `${coverage.toFixed(0)}%`], ['Images', analytics.images_captured], ['Defects', defects]].map(([l, v]) => (
                      <div key={l as string}>
                        <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: 'var(--amber)' }}>{v}</div>
                        <div style={{ fontSize: 8, letterSpacing: 2, color: 'var(--text-lo)' }}>{l}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Fleet cards */}
          <div>
            <div className="section-header"><div className="section-title">Fleet Status</div></div>
            <div className="page-grid-3" style={{ gap: 10 }}>
              {drones.map(d => <DroneCard key={d.id} drone={d} />)}
            </div>
          </div>

          {/* Severity breakdown */}
          {analytics && sevTotal > 0 && (
            <div className="card">
              <div className="card-title">Defect Severity Distribution</div>
              <SevBar label="LOW"      count={sevMap.low ?? 0}      total={sevTotal} color="var(--green)" />
              <SevBar label="MEDIUM"   count={sevMap.medium ?? 0}   total={sevTotal} color="var(--yellow)" />
              <SevBar label="HIGH"     count={sevMap.high ?? 0}     total={sevTotal} color="var(--amber)" />
              <SevBar label="CRITICAL" count={sevMap.critical ?? 0} total={sevTotal} color="var(--red)" />
            </div>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="card" style={{ flex: 1 }}>
            <div className="card-title">System Events</div>
            <div className="event-log">
              {events.slice(0, 50).map(ev => (
                <div key={ev.id} className={`event-entry ${ev.level}`}>
                  <span className="event-ts">{ev.ts.slice(11, 19)}</span>
                  <span className="event-msg">{ev.message}</span>
                </div>
              ))}
              {events.length === 0 && <div className="text-dim" style={{ fontSize: 10, padding: '8px 0' }}>No events</div>}
            </div>
          </div>

          <div className="card">
            <div className="card-title">Mission Log</div>
            {missions.slice(0, 7).map(m => (
              <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid rgba(20,50,69,0.5)' }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600 }}>{m.name}</div>
                  <div style={{ fontSize: 9, color: 'var(--text-lo)', letterSpacing: 1 }}>{m.created_at.slice(0, 10)} · {m.waypoints.length} WPs</div>
                </div>
                <span className={`badge badge-${m.status}`}>{m.status}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-title">Asset Health Matrix</div>
            {assets.slice(0, 8).map(a => {
              const c = a.condition_score >= 80 ? 'var(--green)' : a.condition_score >= 50 ? 'var(--yellow)' : 'var(--red)';
              return (
                <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 0', borderBottom: '1px solid rgba(20,50,69,0.4)' }}>
                  <div style={{ fontSize: 11, flex: 1, color: 'var(--text-mid)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.name}</div>
                  <div style={{ width: 60, height: 3, background: 'var(--hull)' }}>
                    <div style={{ width: `${a.condition_score}%`, height: '100%', background: c }} />
                  </div>
                  <span className="mono" style={{ fontSize: 10, minWidth: 28, color: c }}>{a.condition_score.toFixed(0)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
