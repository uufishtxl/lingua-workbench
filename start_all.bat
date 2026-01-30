@echo off
echo Starting Lingua Workbench Services...

:: Backend
start "Lingua Backend" cmd /k "cd backend && call venv\Scripts\activate && python manage.py runserver 0.0.0.0:8000"

:: Frontend
start "Lingua Frontend" cmd /k "cd frontend && npm run dev"

:: Whisper API
start "Whisper API" cmd /k "cd whisper && uv run uvicorn whisper_api:app --reload --port 8001"

:: Huey Consumer
start "Huey Worker" cmd /k "cd whisper && uv run huey_consumer tasks.huey"

echo All services started!
