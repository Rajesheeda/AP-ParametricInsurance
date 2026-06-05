@echo off
echo ==========================================
echo Starting AP-CropGuard Backend and Frontend
echo ==========================================

echo Starting Python FastAPI Backend on http://127.0.0.1:8000 ...
start cmd /k "cd backend && py -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo Starting Vite React Frontend on http://127.0.0.1:3000 ...
start cmd /k "cd frontend && npm run dev"

echo.
echo Both servers have been launched in separate terminal windows.
echo - Backend API: http://127.0.0.1:8000/docs (FastAPI Swagger Docs)
echo - Frontend Dashboard: http://127.0.0.1:3000/
echo.
pause
