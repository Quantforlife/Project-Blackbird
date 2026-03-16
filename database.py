import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { useStore } from './store';
import { getDrones, getMissions, getAssets } from './utils/api';
import { useFleetWebSocket, useEventsWebSocket } from './hooks/useWebSocket';

import Dashboard      from './pages/Dashboard';
import MissionPlanner from './pages/MissionPlanner';
import LiveView       from './pages/LiveView';
import Fleet          from './pages/Fleet';
import Inspections    from './pages/Inspections';
import AnnotationTool from './pages/AnnotationTool';
import DigitalTwin    from './pages/DigitalTwin';
import Reports        from './pages/Reports';

import './App.css';

const NAV = [
  { path: '/',            icon: '⬡', label: 'Dashboard' },
  { path: '/live',        icon: '◉', label: 'Live Ops' },
  { path: '/missions',    icon: '◎', label: 'Missions' },
  { path: '/fleet',       icon: '◈', label: 'Fleet' },
  { path: '/inspections', icon: '◫', label: 'Inspections' },
  { path: '/annotate',    icon: '◧', label: 'Annotate' },
  { path: '/twin',        icon: '◬', label: 'Digital Twin' },
  { path: '/reports',     icon: '◪', label: 'Reports' },
];

// ── Clocks ──────────────────────────────────────────────────────────────────
function useClock(missionStart: number) {
  const [zulu, setZulu]    = useState('');
  const [mission, setMiss] = useState('00:00:00');

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setZulu(now.toUTCString().slice(17, 25));
      const ms = Date.now() - missionStart;
      const h  = Math.floor(ms / 3600000);
      const m  = Math.floor((ms % 3600000) / 60000);
      const s  = Math.floor((ms % 60000) / 1000);
      setMiss(
        `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
      );
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [missionStart]);

  return { zulu, mission };
}

// ── Global data loader ───────────────────────────────────────────────────────
function GlobalBootstrap() {
  const { setDrones, setMissions, setAssets, addEvent } = useStore();
  useFleetWebSocket();
  useEventsWebSocket();

  useEffect(() => {
    const load = async () => {
      try {
        const [drones, missions, assets] = await Promise.all([
          getDrones(), getMissions(), getAssets(),
        ]);
        setDrones(drones);
        setMissions(missions);
        setAssets(assets);
        addEvent('system', `${drones.length} drones · ${missions.length} missions loaded`, 'success');
      } catch {
        addEvent('system', 'Backend unreachable — retrying in 5s', 'error');
        setTimeout(load, 5000);
      }
    };
    load();
    const interval = setInterval(async () => {
      try {
        const [drones, missions] = await Promise.all([getDrones(), getMissions()]);
        setDrones(drones);
        setMissions(missions);
      } catch {}
    }, 15000);
    return () => clearInterval(interval);
  }, [setDrones, setMissions, setAssets, addEvent]);

  return null;
}

// ── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar() {
  const { drones, wsConnected } = useStore();
  const activeDrones = drones.filter(d => d.status === 'flying').length;

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-hex" />
        <div>
          <div className="brand-name">BLACKBIRD</div>
          <div className="brand-sub">ARES · v3</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className={`ws-indicator ${wsConnected ? 'connected' : 'disconnected'}`}>
          <span className="ws-dot" />
          <span className="ws-label">{wsConnected ? 'COMMS LIVE' : 'OFFLINE'}</span>
        </div>
        {activeDrones > 0 && (
          <div className="active-drones-badge">{activeDrones} AIRBORNE</div>
        )}
      </div>
    </aside>
  );
}

// ── Masthead ─────────────────────────────────────────────────────────────────
function Masthead() {
  const { drones, missions, recentDetections, wsConnected } = useStore();
  const location = useLocation();

  const missionStart = React.useRef(Date.now());
  const { zulu, mission } = useClock(missionStart.current);

  const flyingDrones   = drones.filter(d => d.status === 'flying').length;
  const activeMissions = missions.filter(m => m.status === 'active').length;
  const pageTitle      = NAV.find(n => n.path === location.pathname)?.label ?? 'Dashboard';

  return (
    <header className="topbar">
      <div className="topbar-title">{pageTitle}</div>

      {/* Zulu + mission clocks */}
      <div style={{ display:'flex', alignItems:'stretch', borderLeft:'1px solid var(--seam)' }}>
        <div className="topbar-stat">
          <span className="ts-val" style={{ fontSize:14, color:'var(--cyan)' }}>{zulu}</span>
          <span className="ts-label">ZULU</span>
        </div>
        <div className="topbar-stat">
          <span className="ts-val" style={{ fontSize:14, color:'var(--amber)' }}>{mission}</span>
          <span className="ts-label">MISSION</span>
        </div>
      </div>

      <div className="topbar-stats">
        <div className="topbar-stat">
          <span className="ts-val flying">{flyingDrones}</span>
          <span className="ts-label">AIRBORNE</span>
        </div>
        <div className="topbar-stat">
          <span className="ts-val active">{activeMissions}</span>
          <span className="ts-label">MISSIONS</span>
        </div>
        <div className="topbar-stat">
          <span className="ts-val defect">{recentDetections.length}</span>
          <span className="ts-label">DEFECTS</span>
        </div>
        <div className={`status-pill ${wsConnected ? 'ok' : 'err'}`}>
          {wsConnected ? 'LIVE' : 'OFFLINE'}
        </div>
      </div>
    </header>
  );
}

// ── Root ─────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <GlobalBootstrap />
      <div className="app-shell">
        <Sidebar />
        <div className="main-area">
          <Masthead />
          <main className="content-area">
            <Routes>
              <Route path="/"             element={<Dashboard />} />
              <Route path="/live"         element={<LiveView />} />
              <Route path="/missions"     element={<MissionPlanner />} />
              <Route path="/fleet"        element={<Fleet />} />
              <Route path="/inspections"  element={<Inspections />} />
              <Route path="/annotate"     element={<AnnotationTool />} />
              <Route path="/twin"         element={<DigitalTwin />} />
              <Route path="/reports"      element={<Reports />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
