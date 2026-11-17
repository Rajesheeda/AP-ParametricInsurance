@echo off
REM Demo launcher: starts the POC backend in its own window (keep that window open during the demo),
REM waits for it to load, then opens the dashboard. Close the "AP POC backend" window to stop it.
cd /d "%~dp0"
start "AP POC backend - keep this window open" cmd /k ""C:\Users\rajes\AppData\Local\Programs\Python\Python313\python.exe" -m uvicorn main:app --app-dir ap-cropguard-backend --host 127.0.0.1 --port 8010"
echo Starting the backend... waiting 45 seconds for the photo layers to load.
timeout /t 45 /nobreak >nul
start "" "http://127.0.0.1:8010/"
echo Dashboard opened. To run the preflight check:  py -3.13 poc\preflight.py
pause
