@echo off
echo ==========================================
echo Starting AP-CropGuard Backend and Frontend
echo ==========================================

echo Starting Python FastAPI Backend on http://localhost:8000 ...
start cmd /k "cd backend && py -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Starting Vite React Frontend on http://localhost:5173 ...
start cmd /k "cd frontend && npm run dev"

echo.
echo Both servers have been launched in separate terminal windows.
echo - Backend API: http://localhost:8000/docs (FastAPI Swagger Docs)
echo - Frontend Dashboard: http://localhost:5173/ or http://localhost:5174/
echo.
pause
