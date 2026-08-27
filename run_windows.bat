@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

if not exist .venv\Scripts\python.exe py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
start "Python in Practice" http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
pause
