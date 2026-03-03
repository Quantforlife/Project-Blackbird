# Project Blackbird Startup Guide

## 1) Create virtual environment

```bash
cd project_blackbird
python -m venv .venv
source .venv/bin/activate
```

## 2) Install requirements

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Environment setup

```bash
cp .env.example .env
```

Update `.env` values as needed.

## 4) Development run

```bash
export FLASK_ENV=development
python run.py
```

## 5) Production run

```bash
export FLASK_ENV=production
python run.py
```

## 6) Gunicorn run

```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:5000 run:app
```

## 7) Enable investor demo mode

```bash
export INVESTOR_DEMO_MODE=True
python run.py
```

## 8) Clear timeline state

Use reset command route:

```bash
curl -X POST http://127.0.0.1:5000/realtime/command/reset
```

## 9) Safe reset / restart sequence

1. Pause active mission:
   ```bash
   curl -X POST http://127.0.0.1:5000/realtime/command/pause
   ```
2. Reset runtime:
   ```bash
   curl -X POST http://127.0.0.1:5000/realtime/command/reset
   ```
3. Restart mission:
   ```bash
   curl -X POST http://127.0.0.1:5000/realtime/command/start
   ```

## Startup Order Enforced in App Factory

1. Initialize extensions
2. Initialize socket
3. Initialize controller
4. Register routes
5. Register event subscriptions
