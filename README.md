# Project Blackbird Repository

This repository contains the runnable app in:

- `project_blackbird/`

## Localhost quick start

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

## If import looks empty in Replit

When importing this repo, set the run command from the `project_blackbird` directory:

```bash
cd project_blackbird && python run.py
```

The app files are intentionally nested under `project_blackbird/`.
