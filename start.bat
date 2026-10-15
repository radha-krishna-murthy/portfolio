@echo off
cd /d "%~dp0backend"
if not exist .venv (
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
start "" http://localhost:8000
.venv\Scripts\python -m uvicorn app:app --port 8000
