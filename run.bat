@echo off
setlocal

set ROOT=%~dp0
cd /d "%ROOT%"

where python >NUL 2>NUL
if errorlevel 1 (
  echo Python 3.10+ is required and was not found on PATH.
  exit /b 1
)

python scripts\bootstrap_venv.py
if errorlevel 1 exit /b 1

.venv\Scripts\python scripts\build_goclone.py --windows
if errorlevel 1 exit /b 1

.venv\Scripts\python -m ui.app
exit /b %errorlevel%
