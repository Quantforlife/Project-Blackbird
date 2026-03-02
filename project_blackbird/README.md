# Project Blackbird – Autonomous Drone Solar Inspection Platform

## 1. Project Overview
Project Blackbird is an autonomous drone inspection platform for utility-scale solar farms. It ingests mission imagery, tracks defect detections, streams simulated telemetry, renders a live command dashboard, and generates investor-ready PDF inspection reports.

## 2. Architecture Diagram
```text
                    +-------------------------+
                    |     Browser Client      |
                    | Dashboard / Terminal UI |
                    +-----------+-------------+
                                |
                                | HTTP + SSE
                                v
+--------------------------- Flask App Factory -----------------------------+
|                                                                           |
|  Blueprints:                                                              |
|  - dashboard_bp   (UI routes)                                             |
|  - api_bp         (upload/report/image/health)                            |
|  - admin_bp       (waitlist admin)                                        |
|  - realtime_bp    (snapshot + SSE stream)                                 |
|                                                                           |
|  Services:                                                                |
|  - TelemetryEngine (thread-safe realtime simulation, 1s tick)             |
|                                                                           |
|  Utilities:                                                               |
|  - DataLogger                                                             |
|  - ReportGenerator (opencv/reportlab optional with valid PDF fallback)    |
|  - AIInference (deterministic fallback in offline mode)                   |
|  - FlightController (simulation fallback)                                 |
|                                                                           |
+-------------------------------+-------------------------------------------+
                                |
                                v
                     SQLite (dev/test) / PostgreSQL (prod)
```

## 3. Tech Stack
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate
- **Realtime**: Server-Sent Events (SSE)
- **Frontend**: Bootstrap 5, Chart.js, Leaflet.js, custom dark terminal theme
- **Reporting**: ReportLab/OpenCV optional + minimal PDF fallback
- **Drone/AI Optional**: MAVSDK, PyMAVLink, Torch, Ultralytics
- **Testing**: Pytest
- **Deployment**: Gunicorn, Procfile, Replit configs

## 4. Setup Instructions
```bash
cd project_blackbird
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open:
- http://127.0.0.1:5000
- http://127.0.0.1:5000/dashboard

## 5. Environment Variables
| Variable | Description | Default |
|---|---|---|
| `FLASK_ENV` | `development/testing/production` | `development` |
| `SECRET_KEY` | Flask secret key (required in production) | `dev-secret-key` |
| `API_KEY` | Upload API auth header value | `blackbird-dev-key` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///blackbird.db` |
| `UPLOAD_FOLDER` | Uploaded images storage path | `uploads` |
| `REPORT_FOLDER` | Generated reports storage path | `reports` |
| `OFFLINE_MODE` | Enables deterministic simulation | `True` |
| `PORT` | Bind port | `5000` |

## 6. Real-time System Explanation
- `TelemetryEngine` starts automatically at app boot.
- Thread-safe in-memory state updates every second.
- SSE endpoint `/realtime/stream` emits telemetry, logs, and defect markers once per second.
- Dashboard JavaScript subscribes to the stream and updates:
  - Battery
  - Flight time
  - Mission progress
  - Defect count
  - Image count
  - Moving map marker + dynamic defect overlays
  - Palantir-style command terminal logs

## 7. Deployment Guide (Render + Gunicorn)
### Render
1. Create new Web Service from repo.
2. Root directory: `project_blackbird`
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
   ```
5. Set environment variables (`SECRET_KEY`, `API_KEY`, `DATABASE_URL`, `OFFLINE_MODE=False` for live mode).

### Local production smoke test
```bash
FLASK_ENV=production SECRET_KEY=change-me PORT=5000 gunicorn run:app --bind 0.0.0.0:5000
```

## 8. Demo Script for Investors
1. Open `/dashboard` and show live telemetry updates (map + metrics + terminal).
2. Upload test images and detection CSV via `/upload` using API key.
3. Open `/flights` and select latest mission.
4. Generate report from flight detail page.
5. Download PDF from `/report/<id>`.
6. Show `/admin/waitlist` and demonstrate lead capture via `/waitlist`.

## 9. Future Roadmap
- Live websocket integration with real drone hardware.
- Multi-tenant RBAC and audit logs.
- Defect severity scoring and predictive maintenance analytics.
- Historical mission playback and geospatial heatmaps.
- S3-compatible object storage and CDN acceleration.

## 10. License
This project is distributed under the terms of the repository `LICENSE` file.


## Real-Time Visualization Architecture
- **Telemetry Flow**: `TelemetryEngine` advances on deterministic waypoints every second, updates mission metrics, and emits synchronized logs + defect events.
- **Stream Transport**: browser subscribes to `GET /realtime/stream` (SSE, `event: telemetry`) and applies one atomic payload per tick.
- **Payload Schema**:
  ```json
  {
    "telemetry": {"latitude": 0, "longitude": 0, "battery": 0, "mission_progress": 0, "mode": "live"},
    "path": [{"idx": 0, "lat": 0, "lon": 0, "alt": 0, "heading": 0, "speed": 0}],
    "defects": [{"id": 1, "lat": 0, "lon": 0, "severity": "critical", "x": 0, "y": 0, "w": 0, "h": 0}],
    "video": {"frame_id": 1, "status": "running", "boxes": []},
    "logs": [{"ts": "12:00:00", "level": "AI", "message": "Thermal anomaly detected"}],
    "analytics": {"critical": 0, "warning": 0, "minor": 0, "total": 0}
  }
  ```
- **Video Overlay Pipeline**: `video_overlay.js` paints synthetic frames on `<canvas>`, then overlays color-coded boxes from `video.boxes` using frame coordinates.
- **Mapping Pipeline**: `map.js` renders mission path polyline, current drone marker, and defect markers; playback scrubber requests `POST /realtime/playback/<index>`.
- **Terminal Pipeline**: `terminal.js` applies timestamped level-colored lines (`INFO/WARN/ERROR/AI/GPS/NET/SYS`) with scanline styling and animated insert.
