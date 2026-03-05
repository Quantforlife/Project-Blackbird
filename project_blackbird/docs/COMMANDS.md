```bash
cd /workspace/Project-Blackbird/project_blackbird
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

```bash
cd /workspace/Project-Blackbird/project_blackbird
source .venv/bin/activate
export FLASK_ENV=development
export FLASK_APP=run.py
python run.py
```

```bash
cd /workspace/Project-Blackbird/project_blackbird
source .venv/bin/activate
export FLASK_ENV=production
export FLASK_APP=run.py
python run.py
```

```bash
cd /workspace/Project-Blackbird/project_blackbird
source .venv/bin/activate
gunicorn -w 2 -k gthread -b 0.0.0.0:5000 run:app
```

```bash
cd /workspace/Project-Blackbird/project_blackbird
source .venv/bin/activate
export INVESTOR_DEMO_MODE=True
python run.py
```

```bash
curl -X POST http://127.0.0.1:5000/realtime/command/start
curl -X POST http://127.0.0.1:5000/realtime/command/pause
curl -X POST http://127.0.0.1:5000/realtime/command/resume
curl -X POST http://127.0.0.1:5000/realtime/command/reset
curl -X POST http://127.0.0.1:5000/realtime/command/end
curl -X POST http://127.0.0.1:5000/realtime/mode/live
curl -X POST http://127.0.0.1:5000/realtime/mode/playback
curl -X POST http://127.0.0.1:5000/realtime/playback/10
```

```bash
curl http://127.0.0.1:5000/realtime/snapshot
curl http://127.0.0.1:5000/realtime/video
curl -N http://127.0.0.1:5000/realtime/stream
```

```bash
cd /workspace/Project-Blackbird/project_blackbird
source .venv/bin/activate
pytest -q
python verify_boot.py
```

```bash
cd /workspace/Project-Blackbird/project_blackbird
source .venv/bin/activate
pkill -f "python run.py"
pkill -f "gunicorn"
```
