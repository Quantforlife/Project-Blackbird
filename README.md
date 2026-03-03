# Project Blackbird Repository

This repository contains the runnable app in:

- `project_blackbird/`

## Windows quick start

```bat
setup.bat
run_app.bat
```

Production mode:

```bat
run_app.bat production
```

## Linux/macOS quick start

```bash
cd project_blackbird
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open:

- http://127.0.0.1:5000
- http://127.0.0.1:5000/dashboard
