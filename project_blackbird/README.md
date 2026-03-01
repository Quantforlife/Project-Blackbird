# Project Blackbird – Autonomous Drone Solar Inspection System

## Setup

### 1) Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

```bash
cp .env.example .env
```

Edit `.env` as needed.

### 4) Database migration initialization

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial"
flask --app run.py db upgrade
```

### 5) Run server

```bash
flask --app run.py run
```

## Example cURL upload

```bash
curl -X POST http://127.0.0.1:5000/upload \
  -H "X-API-Key: blackbird-dev-key" \
  -F "name=Inspection 01" \
  -F "location=Solar Farm A" \
  -F "latitude=37.7749" \
  -F "longitude=-122.4194" \
  -F "images=@sample1.jpg" \
  -F "images=@sample2.jpg" \
  -F "detections=@detections.csv"
```

`detections.csv` format:

```csv
filename,defect_type,confidence,x,y
sample1.jpg,hotspot,0.95,120,80
sample2.jpg,crack,0.88,210,130
```

## Run tests

```bash
pytest -q
```

## Production DB (PostgreSQL)

Set:

```bash
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/project_blackbird
```
