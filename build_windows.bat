@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --clean --onedir --name PythonInPractice --add-data "templates;templates" --add-data "static;static" app.py

echo.
echo Build complete: dist\PythonInPractice\PythonInPractice.exe
pause
