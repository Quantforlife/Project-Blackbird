@echo off
setlocal

cd /d "%~dp0"
set "APP_DIR=%CD%\project_blackbird"

if not exist "%APP_DIR%\.venv\Scripts\activate.bat" (
  echo Virtual environment missing. Run setup.bat first.
  exit /b 1
)

call "%APP_DIR%\.venv\Scripts\activate.bat"
cd /d "%APP_DIR%"

if /I "%1"=="production" (
  set FLASK_ENV=production
) else (
  set FLASK_ENV=development
)

set FLASK_APP=run.py

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do taskkill /PID %%p /F >nul 2>nul

python run.py
