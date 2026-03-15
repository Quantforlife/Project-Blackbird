import React from 'react';
import { useStore } from '../store';

function BatBar({ pct }: { pct: number }) {
  const c = pct > 60 ? 'var(--green)' : pct > 30 ? 'var(--yellow)' : 'var(--red)';
  return (
    <div className="battery-bar-wrap">
      <div className="battery-bar"><div className="battery-fill" style={{ width: `${pct}%`, background: c }} /></div>
      <span className="battery-val mono" style={{ color: c }}>{pct.toFixed(0)}%</span>
    </div>
  );
}

const DRONE_COLORS = ['var(--cyan)', 'var(--amber)', 'var(--green)'];

export default function Fleet() {
  const { drones, telemetry } = useStore();
  const flying   = drones.filter(d => d.status === 'flying').length;
  const idle     = drones.filter(d => d.status === 'idle').length;
  const offline  = drones.filter(d => d.status === 'error' || d.status === 'offline').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="page-grid-4">
        <div className="stat-card"><div className="stat-val">{drones.length}</div><div className="stat-label">Total Fleet</div></div>
        <div className="stat-card green"><div className="stat-val text-green">{flying}</div><div className="stat-label">Airborne</div></div>
        <div className="stat-card"><div className="stat-val" style={{ color: 'var(--cyan)' }}>{idle}</div><div className="stat-label">Standby</div></div>
        <div className="stat-card red"><div className="stat-val text-red">{offline}</div><div className="stat-label">Offline / Error</div></div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Unit ID</th><th>Model</th><th>Status</th><th>Battery</th>
              <th>Position</th><th>Altitude</th><th>Speed</th><th>Signal</th><th>Last Contact</th>
            </tr>
          </thead>
          <tbody>
            {drones.map((drone, idx) => {
              const t   = telemetry[drone.id];
              const col = DRONE_COLORS[idx % DRONE_COLORS.length];
              return (
                <tr key={drone.id}>
                  <td>
                    <div style={{ fontWeight: 700, color: col }}>{drone.name}</div>
                    <div style={{ fontSize: 9, color: 'var(--text-lo)', fontFamily: 'var(--f-mono)' }}>{drone.id.slice(0, 8)}</div>
                  </td>
                  <td style={{ color: 'var(--text-mid)', fontSize: 11 }}>{drone.model}</td>
                  <td><span className={`badge badge-${drone.status}`}>{drone.status}</span></td>
                  <td style={{ minWidth: 130 }}><BatBar pct={t?.battery_pct ?? drone.battery_pct} /></td>
                  <td className="mono" style={{ fontSize: 10 }}>
                    {t ? `${t.lat.toFixed(4)}, ${t.lon.toFixed(4)}` : '—'}
                  </td>
                  <td className="mono" style={{ fontSize: 11 }}>{t ? `${t.altitude_m.toFixed(0)}m` : '—'}</td>
                  <td className="mono" style={{ fontSize: 11 }}>{t ? `${t.speed_ms.toFixed(1)}m/s` : '—'}</td>
                  <td className="mono" style={{ fontSize: 11, color: t && t.signal_dbm > -70 ? 'var(--green)' : 'var(--yellow)' }}>
                    {t ? `${t.signal_dbm.toFixed(0)}dBm` : '—'}
                  </td>
                  <td style={{ fontSize: 10, color: 'var(--text-mid)' }}>
                    {drone.last_seen ? new Date(drone.last_seen).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="page-grid-3">
        {drones.map((drone, idx) => {
          const t   = telemetry[drone.id];
          const col = DRONE_COLORS[idx % DRONE_COLORS.length];
          return (
            <div key={drone.id} className="card" style={{ borderLeft: `2px solid ${col}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: 16, color: col, letterSpacing: 1 }}>{drone.name}</div>
                  <div style={{ fontSize: 9, color: 'var(--text-lo)', letterSpacing: 1 }}>FW {drone.firmware}</div>
                </div>
                <span className={`badge badge-${drone.status}`}>{drone.status}</span>
              </div>
              {t ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
                  {[['Alt', `${t.altitude_m.toFixed(0)}m`], ['Speed', `${t.speed_ms.toFixed(1)}m/s`],
                    ['Hdg', `${t.heading_deg.toFixed(0)}°`], ['Roll', `${t.roll_deg.toFixed(1)}°`],
                    ['Pitch', `${t.pitch_deg.toFixed(1)}°`], ['Sats', t.gps_sats],
                  ].map(([k, v]) => (
                    <div key={k as string} style={{ textAlign: 'center', padding: '7px 4px', background: 'var(--hull)', clipPath: 'var(--clip-sm)' }}>
                      <div className="mono" style={{ fontSize: 14, fontWeight: 700, color: col }}>{v}</div>
                      <div style={{ fontSize: 7, letterSpacing: 2, color: 'var(--text-lo)', marginTop: 2 }}>{k}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 10, color: 'var(--text-lo)', letterSpacing: 2 }}>AWAITING TELEMETRY</div>
              )}
              <div style={{ marginTop: 10 }}>
                <BatBar pct={t?.battery_pct ?? drone.battery_pct} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
