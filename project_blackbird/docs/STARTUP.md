# Project Blackbird Startup (Windows-first)

## One-command setup

```bat
setup.bat
```

## One-command launch

```bat
run_app.bat
```

## Launch in production mode

```bat
run_app.bat production
```

## Environment variables

- `FLASK_APP`: Flask entrypoint module (`run.py`).
- `FLASK_ENV`: Runtime mode (`development`, `production`, or `testing`).
- `SECRET_KEY`: Flask secret key used for sessions/security.
- `API_KEY`: API key used by protected API endpoints.
- `DATABASE_URL`: SQLAlchemy DB connection string.
- `UPLOAD_FOLDER`: Upload directory path.
- `REPORT_FOLDER`: Report output directory path.
- `OFFLINE_MODE`: Enables deterministic offline telemetry/perception stubs (`True`/`False`).
- `INVESTOR_DEMO_MODE`: Auto-starts live mission at app boot (`True`/`False`).
- `PORT`: HTTP port used by `run.py`.

## Troubleshooting

### `run_app.bat` says virtualenv is missing

```bat
setup.bat
```

### Python launcher not found

Install Python 3.10+ from python.org and ensure `py` is available in PATH, then run:

```bat
setup.bat
```

### Port 5000 already in use

`run_app.bat` attempts to kill stale listeners automatically, then starts the app again.

### Verify installation manually

```bat
cd project_blackbird
.venv\Scripts\activate.bat
python verify_boot.py
pytest -q
```
