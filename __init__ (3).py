# Project Blackbird — Alpha 1

**Autonomous Drone Inspection Platform for Infrastructure Assets**

> Solar farms · Wind turbines · Power lines · Industrial facilities

---

## Overview

Project Blackbird Alpha 1 is a full-stack autonomous drone inspection system featuring:

- **Multi-drone simulation** with PID flight controllers and realistic telemetry at 10 Hz
- **Real-time dashboard** with live map, fleet telemetry, and defect detection
- **Computer vision pipeline** using YOLOv8 for automated defect detection
- **Digital twin** — Three.js 3D visualization of assets color-coded by condition
- **PDF report generation** with ReportLab
- **TimescaleDB** hypertable for high-throughput telemetry storage
- **WebSocket streaming** via Redis pub/sub for horizontal scalability

---

## Architecture

```
┌─────────────┐    WebSocket/REST    ┌──────────────────────┐
│   Frontend  │◄──────────────────►  │   FastAPI Backend    │
│  React/TS   │                      │   (uvicorn)          │
│  Port 3000  │                      │   Port 8000          │
└─────────────┘                      └──────┬───────────────┘
                                            │
                              ┌─────────────┼─────────────┐
                              │             │             │
                    ┌─────────▼──┐  ┌───────▼──┐  ┌──────▼──────┐
                    │ PostgreSQL │  │  Redis   │  │   Celery    │
                    │+TimescaleDB│  │ Pub/Sub  │  │   Worker    │
                    │  Port 5432 │  │ Port 6379│  │  (YOLOv8)   │
                    └────────────┘  └──────────┘  └─────────────┘
                                            ▲
                                   ┌────────┴────────┐
                                   │   Simulation    │
                                   │  (3 drones,     │
                                   │   PID physics)  │
                                   └─────────────────┘
```

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- 4GB RAM minimum (8GB recommended)
- Ports 3000, 5432, 6379, 8000 available

### 1. Clone and configure

```bash
git clone <repo>
cd blackbird
cp .env.example .env
# Edit .env if needed (defaults work out of the box)
```

### 2. Start all services

```bash
docker compose up --build
```

This starts:
| Service    | URL                       | Description                    |
|------------|---------------------------|--------------------------------|
| Frontend   | http://localhost:3000     | React dashboard                |
| Backend    | http://localhost:8000     | FastAPI + WebSocket            |
| API Docs   | http://localhost:8000/docs | Swagger UI                    |
| PostgreSQL | localhost:5432            | TimescaleDB                    |
| Redis      | localhost:6379            | Pub/Sub + Celery broker        |

### 3. Verify

```bash
# Health check
curl http://localhost:8000/health

# List drones (auto-seeded on first run)
curl http://localhost:8000/drones

# Run E2E test
docker compose exec backend python tests/e2e_test.py
```

The simulation starts automatically and runs missions continuously. Open http://localhost:3000 to see live drone telemetry on the dashboard.

---

## Project Structure

```
blackbird/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic settings
│   │   │   ├── database.py        # Async SQLAlchemy engine
│   │   │   ├── redis_client.py    # Redis pub/sub
│   │   │   └── security.py        # API key auth
│   │   ├── models/
│   │   │   └── models.py          # All ORM models (8 tables)
│   │   ├── schemas/
│   │   │   └── schemas.py         # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── missions.py        # POST/GET/start/pause/stop
│   │   │   ├── drones.py          # Fleet management + telemetry ingestion
│   │   │   ├── images.py          # Upload + file serving
│   │   │   ├── detections.py      # CRUD + manual annotation
│   │   │   ├── assets.py          # Asset management + inspection history
│   │   │   ├── reports.py         # PDF generation + download
│   │   │   └── websocket.py       # /ws/drone/{id}, /ws/fleet, /ws/events
│   │   ├── tasks/
│   │   │   ├── celery_app.py      # Celery configuration
│   │   │   ├── detection_tasks.py # YOLOv8 inference worker
│   │   │   └── report_tasks.py    # ReportLab PDF generation
│   │   └── main.py                # FastAPI entrypoint + seeding
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 0001_initial.py    # Schema + TimescaleDB hypertable
│   │   └── env.py
│   ├── tests/
│   │   ├── test_physics.py        # Drone physics unit tests
│   │   ├── test_api.py            # API endpoint tests (async)
│   │   ├── test_detection.py      # CV pipeline tests
│   │   └── e2e_test.py            # End-to-end integration test
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-test.txt
│
├── simulation/
│   ├── physics.py     # PID FlightController + DroneState
│   ├── renderer.py    # Headless synthetic image generator (Pillow)
│   ├── main.py        # Multi-drone orchestrator
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx      # KPIs, fleet cards, event feed
│   │   │   ├── MissionPlanner.tsx # Leaflet map, waypoint drawing
│   │   │   ├── LiveView.tsx       # Real-time map + telemetry panels
│   │   │   ├── Fleet.tsx          # Fleet table + drone detail cards
│   │   │   ├── Inspections.tsx    # Image gallery + detection overlay
│   │   │   ├── AnnotationTool.tsx # Canvas bbox drawing tool
│   │   │   ├── DigitalTwin.tsx    # Three.js 3D asset visualization
│   │   │   └── Reports.tsx        # PDF generation + download
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts    # Fleet + events WebSocket hooks
│   │   ├── store/
│   │   │   └── index.ts           # Zustand global state
│   │   ├── utils/
│   │   │   └── api.ts             # All API calls (axios)
│   │   ├── types/
│   │   │   └── index.ts           # TypeScript domain types
│   │   ├── App.tsx                # Routing + sidebar + header
│   │   └── App.css                # Dark industrial design system
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── docker/
│   └── init.sql                   # TimescaleDB extension init
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Environment Variables

| Variable              | Default                | Description                     |
|-----------------------|------------------------|---------------------------------|
| `POSTGRES_USER`       | `blackbird`            | Database user                   |
| `POSTGRES_PASSWORD`   | `blackbird_secret`     | Database password               |
| `POSTGRES_DB`         | `blackbird`            | Database name                   |
| `REDIS_URL`           | `redis://redis:6379/0` | Redis connection                |
| `API_KEY`             | `blackbird-alpha-key`  | Internal API key                |
| `DEBUG`               | `true`                 | Enables SQL logging + open auth |
| `NUM_DRONES`          | `3`                    | Simulated drone count           |
| `REACT_APP_API_URL`   | `http://localhost:8000`| Frontend → backend URL          |
| `REACT_APP_WS_URL`    | `ws://localhost:8000`  | WebSocket URL                   |

---

## API Reference

### Missions
| Method | Path                          | Description              |
|--------|-------------------------------|--------------------------|
| POST   | `/missions`                   | Create mission           |
| GET    | `/missions`                   | List all missions        |
| GET    | `/missions/{id}`              | Get mission details      |
| POST   | `/missions/{id}/start`        | Start / resume           |
| POST   | `/missions/{id}/pause`        | Pause                    |
| POST   | `/missions/{id}/stop`         | Abort                    |
| GET    | `/missions/{id}/analytics`    | KPIs and analytics       |
| GET    | `/missions/{id}/images`       | Images captured          |

### Drones
| Method | Path                              | Description              |
|--------|-----------------------------------|--------------------------|
| GET    | `/drones`                         | List fleet               |
| POST   | `/drones`                         | Register drone           |
| GET    | `/drones/{id}/telemetry/latest`   | Latest telemetry frame   |
| GET    | `/drones/{id}/telemetry/history`  | Time-series telemetry    |
| POST   | `/drones/{id}/telemetry`          | Ingest telemetry (sim)   |

### Images & Detections
| Method | Path                        | Description              |
|--------|-----------------------------|--------------------------|
| POST   | `/images`                   | Upload image (multipart) |
| GET    | `/images/{id}/file`         | Serve image file         |
| GET    | `/images/{id}/detections`   | Detections for image     |
| POST   | `/detections`               | Manual annotation        |
| PUT    | `/detections/{id}`          | Update annotation        |
| DELETE | `/detections/{id}`          | Remove annotation        |

### Assets & Reports
| Method | Path                      | Description              |
|--------|---------------------------|--------------------------|
| GET    | `/assets`                 | List all assets          |
| POST   | `/assets`                 | Create asset             |
| GET    | `/assets/{id}/history`    | Inspection history       |
| POST   | `/reports/{mission_id}`   | Queue PDF report         |
| GET    | `/reports/{mission_id}/download` | Download PDF      |

### WebSocket
| Path                  | Description                                |
|-----------------------|--------------------------------------------|
| `/ws/drone/{id}`      | Telemetry stream for specific drone        |
| `/ws/fleet`           | All drones telemetry (pattern subscribe)   |
| `/ws/events`          | System events (missions, detections)       |

---

## Running Tests

```bash
# Unit + API tests
docker compose exec backend pip install -r requirements-test.txt
docker compose exec backend pytest tests/test_physics.py tests/test_api.py tests/test_detection.py -v

# E2E test (requires running backend)
docker compose exec backend python tests/e2e_test.py

# With coverage
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

---

## Development (local, no Docker)

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-test.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Simulation (separate terminal)
cd simulation
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 python main.py

# Frontend
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

---

## Helix Loop — Self-Learning Architecture

The Helix Loop is the continuous improvement cycle:

```
Flight Data
    │
    ▼
[ Onboard Capture ] → compressed image + telemetry
    │
    ▼
[ Offload to Server ] → POST /images, POST /drones/{id}/telemetry
    │
    ▼
[ Celery Worker ] → YOLOv8 inference → store detections
    │
    ▼
[ Asset Condition Update ] → degrade condition score
    │
    ▼
[ Report Generation ] → PDF with full inspection data
    │
    ▼
[ Model Retraining ] ← labeled annotations from /annotate
    │
    ▼
[ Quantized Model Deploy ] → updated weights to drone SDK
    │
    └──────────────► Next Flight
```

---

## Design Decisions

- **TimescaleDB hypertable** on `telemetry.time` — handles thousands of rows/sec with automatic partitioning and compression.
- **Redis pub/sub** for WebSocket fan-out — a single telemetry write from the simulation broadcasts to all connected browsers without direct coupling.
- **Celery + Redis broker** — image processing is fully async; the upload endpoint returns immediately and detection happens in background.
- **Seeded RNG in simulation** — `SyntheticRenderer(seed=42)` ensures reproducible test imagery.
- **PID flight controller** — three independent PID loops (X, Y, Z) with anti-windup produce smooth, physical flight paths with configurable speed and acceleration limits.
- **COCO → defect mapping** — the demo maps COCO class names to solar defect types so YOLOv8n.pt works without custom training. Replace with a trained solar defect model for production.

---

## Roadmap to Beta

- [ ] JWT authentication + RBAC
- [ ] Train custom YOLOv8 model on real solar defect dataset (SOTERIA, PV-Defects)
- [ ] Waypoint auto-generation from uploaded site shapefile / GeoJSON
- [ ] 3D path planning with obstacle avoidance
- [ ] Onboard edge inference (ONNX quantized model)
- [ ] Multi-site support with per-site asset databases
- [ ] Mobile-responsive layout improvements
- [ ] Grafana dashboard for TimescaleDB metrics

---

*Project Blackbird Alpha-1 · Built with FastAPI, React, TimescaleDB, Redis, Celery, Three.js*
