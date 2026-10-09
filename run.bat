@echo off
echo =========================================================================
echo KRISHIRAKSHA AI - Heavy Rainfall & Flood Risk Early Warning System
echo =========================================================================
echo.
echo [1/2] Checking database and ML champion model...
call powershell.cmd -Command "python -m backend.app.seed"

echo.
echo [2/2] Launching Application Server on http://localhost:8000 ...
call powershell.cmd -Command "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
