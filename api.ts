@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600;700;800&family=Share+Tech+Mono&display=swap');

/* ═══════════════════════════════════════════════════════════════════════════
   PROJECT BLACKBIRD — ARES DESIGN SYSTEM v3
   Palette: deep steel / amber active / cyan acquire / red critical
   Font: Barlow Condensed (display) + Share Tech Mono (data)
   Geometry: clip-path panels, no border-radius, armour-plate aesthetic
═══════════════════════════════════════════════════════════════════════════ */

:root {
  --void:      #010507;
  --abyss:     #030c10;
  --steel:     #071520;
  --hull:      #0b1e2e;
  --plating:   #0f2438;
  --seam:      #143245;
  --wire:      #1c4060;
  --amber:     #e8860a;
  --amber2:    #f5a020;
  --amber-dim: rgba(232,134,10,0.12);
  --amber-glow:rgba(232,134,10,0.22);
  --cyan:      #00c8e0;
  --cyan2:     #0099b0;
  --cyan-dim:  rgba(0,200,224,0.1);
  --green:     #00e05a;
  --green-dim: rgba(0,224,90,0.1);
  --red:       #e02040;
  --red-dim:   rgba(224,32,64,0.1);
  --yellow:    #e0c000;
  --yellow-dim:rgba(224,192,0,0.1);
  --purple:    #8060e0;
  --text-hi:   #d0e8f4;
  --text-mid:  #5a8aa8;
  --text-lo:   #2a4858;
  --f-display: 'Barlow Condensed', sans-serif;
  --f-mono:    'Share Tech Mono', monospace;
  --clip-lg:   polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px));
  --clip-md:   polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
  --clip-sm:   polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px));
  --clip-tag:  polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 0 100%);
  --clip-btn:  polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px);
  --sidebar-w: 188px;
  --topbar-h:  46px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, #root {
  height: 100%;
  background: var(--void);
  color: var(--text-hi);
  font-family: var(--f-display);
  font-size: 13px;
  line-height: 1.5;
  overflow: hidden;
}

body::after {
  content: '';
  position: fixed; inset: 0;
  background: repeating-linear-gradient(0deg, transparent 0px, transparent 3px, rgba(0,200,224,0.006) 3px, rgba(0,200,224,0.006) 4px);
  pointer-events: none;
  z-index: 9000;
}

::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: var(--abyss); }
::-webkit-scrollbar-thumb { background: var(--wire); }

/* ── Shell ── */
.app-shell { display: flex; height: 100vh; overflow: hidden; }
.main-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.content-area { flex: 1; overflow-y: auto; overflow-x: hidden; padding: 16px 20px; background: var(--void); }

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-w);
  background: var(--abyss);
  border-right: 1px solid var(--seam);
  display: flex; flex-direction: column;
  flex-shrink: 0; z-index: 100; position: relative;
}
.sidebar::before {
  content: ''; position: absolute; top: 0; left: 0; bottom: 0; width: 2px;
  background: linear-gradient(180deg, var(--amber) 0%, var(--cyan) 50%, transparent 100%);
}
.sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 13px 14px 13px 18px;
  border-bottom: 1px solid var(--seam); flex-shrink: 0;
}
.brand-hex {
  width: 30px; height: 30px;
  background: var(--amber);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--f-mono); font-size: 9px; color: #000;
  flex-shrink: 0; position: relative;
}
.brand-hex::after {
  content: ''; position: absolute; inset: 4px; background: var(--abyss);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}
.brand-name { font-size: 14px; font-weight: 800; letter-spacing: 4px; color: var(--text-hi); line-height: 1; }
.brand-sub  { font-family: var(--f-mono); font-size: 8px; letter-spacing: 2px; color: var(--amber); line-height: 1; margin-top: 2px; }
.sidebar-nav { flex: 1; padding: 8px 6px; display: flex; flex-direction: column; gap: 1px; overflow-y: auto; }
.nav-item {
  display: flex; align-items: center; gap: 9px; padding: 8px 10px;
  color: var(--text-lo); text-decoration: none;
  font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
  transition: all 0.12s; border: 1px solid transparent; position: relative;
}
.nav-item::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
  background: var(--amber); transform: scaleY(0); transition: transform 0.12s;
}
.nav-item:hover { color: var(--text-mid); background: rgba(28,64,96,0.3); }
.nav-item.active { color: var(--amber); background: var(--amber-dim); border-color: rgba(232,134,10,0.2); }
.nav-item.active::before { transform: scaleY(1); }
.nav-icon { font-size: 13px; flex-shrink: 0; }
.sidebar-footer { padding: 10px 14px; border-top: 1px solid var(--seam); display: flex; flex-direction: column; gap: 5px; flex-shrink: 0; }
.ws-indicator { display: flex; align-items: center; gap: 6px; }
.ws-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.ws-indicator.connected .ws-dot { background: var(--green); box-shadow: 0 0 6px var(--green); animation: pdot 2s ease-in-out infinite; }
.ws-indicator.disconnected .ws-dot { background: var(--red); }
@keyframes pdot { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.ws-label { font-family: var(--f-mono); font-size: 9px; letter-spacing: 2px; color: var(--text-lo); }
.active-drones-badge {
  font-family: var(--f-mono); font-size: 8px; letter-spacing: 2px; color: var(--green);
  padding: 3px 8px; clip-path: var(--clip-tag);
  background: var(--green-dim); border: 1px solid rgba(0,224,90,0.25);
}

/* ── Topbar ── */
.topbar {
  height: var(--topbar-h); background: var(--abyss);
  border-bottom: 1px solid var(--seam);
  display: flex; align-items: stretch; flex-shrink: 0; position: relative;
}
.topbar::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--amber) 0%, var(--cyan) 35%, transparent 65%);
}
.topbar-title {
  display: flex; align-items: center; padding: 0 20px;
  font-size: 11px; font-weight: 600; letter-spacing: 4px; color: var(--text-hi);
  text-transform: uppercase; border-right: 1px solid var(--seam); min-width: 180px;
}
.topbar-stats { display: flex; align-items: stretch; margin-left: auto; }
.topbar-stat { display: flex; flex-direction: column; justify-content: center; padding: 0 16px; border-left: 1px solid var(--seam); text-align: center; }
.ts-val { font-family: var(--f-mono); font-size: 18px; font-weight: 500; line-height: 1; }
.ts-label { font-size: 7px; letter-spacing: 2px; color: var(--text-lo); margin-top: 2px; text-transform: uppercase; }
.ts-val.flying { color: var(--green); }
.ts-val.active { color: var(--cyan); }
.ts-val.defect { color: var(--red); }
.status-pill {
  display: flex; align-items: center; gap: 6px; padding: 0 16px;
  font-family: var(--f-mono); font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  border-left: 1px solid var(--seam);
}
.status-pill.ok  { color: var(--green); background: var(--green-dim); }
.status-pill.err { color: var(--red);   background: var(--red-dim); }
.status-pill::before {
  content: ''; width: 5px; height: 5px; border-radius: 50%;
  background: currentColor; box-shadow: 0 0 6px currentColor;
  animation: pdot 2s ease-in-out infinite;
}

/* ── Card ── */
.card {
  background: var(--steel); border: 1px solid var(--seam);
  clip-path: var(--clip-md); padding: 14px 16px; position: relative;
}
.card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--amber) 0%, transparent 60%); opacity: 0.5;
}
.card-title {
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--text-lo); margin-bottom: 12px;
  display: flex; align-items: center; gap: 8px;
}
.card-title::before { content: ''; display: block; width: 12px; height: 1px; background: var(--amber); }

/* ── Stat Card ── */
.stat-card {
  background: var(--steel); border: 1px solid var(--seam);
  clip-path: var(--clip-md); padding: 14px 16px;
  display: flex; flex-direction: column; gap: 3px; position: relative; overflow: hidden;
}
.stat-card::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px;
  background: var(--accent-line, var(--cyan)); opacity: 0.5;
}
.stat-card.green::after  { --accent-line: var(--green); }
.stat-card.red::after    { --accent-line: var(--red); }
.stat-card.yellow::after { --accent-line: var(--yellow); }
.stat-card.amber::after  { --accent-line: var(--amber); }
.stat-val   { font-family: var(--f-mono); font-size: 28px; font-weight: 500; color: var(--text-hi); line-height: 1; }
.stat-label { font-size: 8px; letter-spacing: 3px; color: var(--text-lo); text-transform: uppercase; }
.stat-sub   { font-size: 10px; color: var(--text-lo); margin-top: 2px; }

/* ── Buttons ── */
.btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 7px 16px;
  font-family: var(--f-display); font-size: 10px; font-weight: 700;
  letter-spacing: 2px; text-transform: uppercase; clip-path: var(--clip-btn);
  cursor: pointer; border: none; transition: all 0.12s; text-decoration: none; flex-shrink: 0;
}
.btn-primary { background: var(--amber); color: #000; }
.btn-primary:hover { background: var(--amber2); }
.btn-outline { background: transparent; color: var(--cyan); box-shadow: inset 0 0 0 1px var(--cyan); }
.btn-outline:hover { background: var(--cyan-dim); }
.btn-danger  { background: var(--red); color: #fff; }
.btn-ghost   { background: var(--plating); color: var(--text-mid); box-shadow: inset 0 0 0 1px var(--seam); }
.btn-ghost:hover { color: var(--text-hi); }
.btn:disabled { opacity: 0.3; cursor: not-allowed; }
.btn-sm { padding: 4px 10px; font-size: 9px; }

/* ── Badges ── */
.badge {
  display: inline-flex; align-items: center; padding: 2px 8px;
  clip-path: var(--clip-tag);
  font-family: var(--f-mono); font-size: 9px; letter-spacing: 1.5px;
  font-weight: 500; text-transform: uppercase;
}
.badge-active    { background: var(--green-dim);  color: var(--green);  }
.badge-idle      { background: var(--cyan-dim);   color: var(--cyan);   }
.badge-flying    { background: var(--cyan-dim);   color: var(--cyan);   }
.badge-charging  { background: var(--yellow-dim); color: var(--yellow); }
.badge-error     { background: var(--red-dim);    color: var(--red);    }
.badge-offline   { background: rgba(28,64,96,0.2);color: var(--text-lo);}
.badge-pending   { background: var(--cyan-dim);   color: var(--text-lo);}
.badge-completed { background: var(--green-dim);  color: var(--green);  }
.badge-paused    { background: var(--amber-dim);  color: var(--amber);  }
.badge-aborted   { background: var(--red-dim);    color: var(--red);    }
.badge-low       { background: var(--green-dim);  color: var(--green);  }
.badge-medium    { background: var(--yellow-dim); color: var(--yellow); }
.badge-high      { background: var(--amber-dim);  color: var(--amber);  }
.badge-critical  { background: var(--red-dim);    color: var(--red);    }

/* ── Tables ── */
.table-container { overflow-x: auto; border: 1px solid var(--seam); clip-path: var(--clip-md); }
table { width: 100%; border-collapse: collapse; }
th {
  padding: 9px 14px; text-align: left; font-size: 8px;
  letter-spacing: 2.5px; text-transform: uppercase; color: var(--text-lo);
  background: var(--hull); border-bottom: 1px solid var(--seam); white-space: nowrap;
}
td { padding: 9px 14px; font-size: 12px; border-bottom: 1px solid rgba(20,50,69,0.5); color: var(--text-hi); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(0,200,224,0.03); }

/* ── Utilities ── */
.mono        { font-family: var(--f-mono); }
.text-accent { color: var(--cyan); }
.text-amber  { color: var(--amber); }
.text-green  { color: var(--green); }
.text-red    { color: var(--red); }
.text-dim    { color: var(--text-mid); }
.text-yellow { color: var(--yellow); }
.page-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.page-grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
.page-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.page-cols   { display: grid; gap: 12px; }
.page-cols-2   { grid-template-columns: 1fr 1fr; }
.page-cols-3   { grid-template-columns: 1fr 1fr 1fr; }
.page-cols-1-2 { grid-template-columns: 1fr 2fr; }
.page-cols-2-1 { grid-template-columns: 2fr 1fr; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.section-title {
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase; color: var(--text-lo);
  display: flex; align-items: center; gap: 8px;
}
.section-title::before { content: ''; display: block; width: 12px; height: 1px; background: var(--amber); }
.battery-bar-wrap { display: flex; align-items: center; gap: 8px; }
.battery-bar { flex: 1; height: 3px; background: var(--hull); overflow: hidden; }
.battery-fill { height: 100%; transition: width 0.5s; }
.battery-val  { font-family: var(--f-mono); font-size: 10px; min-width: 34px; }
.loader { display: flex; align-items: center; justify-content: center; height: 200px; color: var(--text-lo); font-family: var(--f-mono); font-size: 10px; letter-spacing: 3px; }
.map-container    { height: 400px; overflow: hidden; clip-path: var(--clip-md); }
.map-container-lg { height: 520px; overflow: hidden; clip-path: var(--clip-md); }
.event-log { display: flex; flex-direction: column; gap: 0; max-height: 280px; overflow-y: auto; }
.event-entry { display: flex; gap: 8px; align-items: flex-start; padding: 5px 0; border-bottom: 1px solid rgba(20,50,69,0.4); font-size: 10px; }
.event-entry:last-child { border-bottom: none; }
.event-ts  { font-family: var(--f-mono); color: var(--text-lo); flex-shrink: 0; }
.event-msg { color: var(--text-mid); }
.event-entry.success .event-msg { color: var(--green); }
.event-entry.warn    .event-msg { color: var(--yellow); }
.event-entry.error   .event-msg { color: var(--red); }
.event-entry.info    .event-msg { color: var(--cyan); }

input, select, textarea {
  background: var(--hull); border: 1px solid var(--seam); color: var(--text-hi);
  padding: 7px 10px; font-family: var(--f-display); font-size: 12px;
  clip-path: var(--clip-sm); outline: none; width: 100%; transition: border-color 0.12s;
}
input:focus, select:focus { border-color: var(--amber); }
input::placeholder { color: var(--text-lo); }
input[type="checkbox"] { width: auto; accent-color: var(--amber); }

.leaflet-container { background: var(--abyss) !important; }
.leaflet-tile { filter: brightness(0.5) saturate(0.4) hue-rotate(175deg); }
.leaflet-control-zoom a { background: var(--steel) !important; color: var(--text-mid) !important; border-color: var(--seam) !important; }

/* ── ARES Primitives ── */
.ares-panel-hdr { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; background: var(--hull); border-bottom: 1px solid var(--seam); flex-shrink: 0; }
.ares-panel-hdr-title { font-size: 8px; letter-spacing: 3px; text-transform: uppercase; color: var(--text-lo); display: flex; align-items: center; gap: 7px; }
.ares-panel-hdr-title::before { content: ''; display: block; width: 10px; height: 1px; background: var(--amber); }
.ares-panel-hdr-count { font-family: var(--f-mono); font-size: 9px; color: var(--amber); }
.tac-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; border-bottom: 1px solid rgba(20,50,69,0.4); }
.tac-row:last-child { border-bottom: none; }
.tac-key { font-size: 8px; letter-spacing: 2px; color: var(--text-lo); text-transform: uppercase; }
.tac-val { font-family: var(--f-mono); font-size: 11px; }
.kpi-cell { background: var(--steel); border: 1px solid var(--seam); clip-path: var(--clip-sm); padding: 10px 14px; display: flex; flex-direction: column; gap: 2px; position: relative; }
.kpi-cell::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 1px; background: var(--kpi-c, var(--cyan)); opacity: 0.5; }
.kpi-val   { font-family: var(--f-mono); font-size: 22px; font-weight: 500; line-height: 1; color: var(--kpi-c, var(--cyan)); }
.kpi-label { font-size: 8px; letter-spacing: 2px; color: var(--text-lo); text-transform: uppercase; }
.sev-row   { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.sev-label { font-size: 9px; letter-spacing: 1px; color: var(--text-lo); width: 54px; }
.sev-track { flex: 1; height: 3px; background: var(--hull); }
.sev-fill  { height: 100%; transition: width 1s ease; }
.sev-count { font-family: var(--f-mono); font-size: 9px; color: var(--text-mid); min-width: 20px; text-align: right; }
.ops-btn { display: flex; align-items: center; gap: 5px; padding: 5px 12px; clip-path: var(--clip-btn); font-family: var(--f-display); font-size: 9px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; cursor: pointer; border: none; transition: all 0.12s; }
.ops-execute { background: var(--amber); color: #000; }
.ops-execute:hover { background: var(--amber2); }
.ops-hold  { background: var(--plating); color: var(--text-mid); box-shadow: inset 0 0 0 1px var(--seam); }
.ops-abort { background: var(--red-dim); color: var(--red); box-shadow: inset 0 0 0 1px rgba(224,32,64,0.3); }
