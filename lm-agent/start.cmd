@echo off
setlocal
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
  echo Python was not found in PATH.
  exit /b 1
)

python -c "import httpx, rich, prompt_toolkit" >nul 2>&1
if errorlevel 1 (
  echo Installing dependencies from requirements.txt...
  python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
)

python agent.py %*
