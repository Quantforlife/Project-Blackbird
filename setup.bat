@echo off
setlocal ENABLEDELAYEDEXPANSION

cd /d "%~dp0"
set "APP_DIR=%CD%\project_blackbird"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.10+ and rerun setup.bat.
  exit /b 1
)

for /f %%v in ('py -3 -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')"') do set "PYVER=%%v"
if "%PYVER%"=="" (
  echo Unable to detect Python version. Install Python 3.10+ and rerun.
  exit /b 1
)
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
  set /a MAJOR=%%a
  set /a MINOR=%%b
)
if %MAJOR% LSS 3 (
  echo Python 3.10+ is required.
  exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 10 (
  echo Python 3.10+ is required.
  exit /b 1
)

echo Detected Python %PYVER%

if not exist "%APP_DIR%\.venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv "%APP_DIR%\.venv"
)

call "%APP_DIR%\.venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r "%APP_DIR%\requirements.txt"

if not exist "%APP_DIR%\.env" (
  copy "%APP_DIR%\.env.example" "%APP_DIR%\.env" >nul
)

cd /d "%APP_DIR%"
set FLASK_APP=run.py
set FLASK_ENV=development
flask db upgrade 2>nul
if errorlevel 1 (
  echo flask db upgrade skipped (migrations may be optional in this environment).
)

python verify_boot.py
if errorlevel 1 (
  echo Boot verification failed.
  exit /b 1
)

echo Setup completed successfully.
exit /b 0
