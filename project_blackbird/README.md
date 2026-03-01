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

## Replit deployment

1. Create a new **Python Repl** and import this repository.
2. Ensure these files are in the project root:
   - `.replit`
   - `replit.nix`
3. In the Replit **Shell**, install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Add Replit Secrets (Tools → Secrets):
   - `SECRET_KEY`
   - `API_KEY`
   - `OFFLINE_MODE` (set to `True` for fully offline-safe behavior)
   - `DATABASE_URL` (`sqlite:///blackbird.db` for simple Replit deploy)
5. Click **Run**. Replit will execute `python run.py` using `.replit`.
6. For Replit Deployments, use the deployment config already in `.replit`.

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
