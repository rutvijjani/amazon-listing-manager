@echo off
echo ==========================================
echo Amazon Listing Manager
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    echo Installing dependencies...
    venv\Scripts\pip.exe install -r requirements.txt
)

echo Starting Flask application...
echo.
echo Access URLs:
echo   Local:   http://127.0.0.1:5000
echo   Network: http://192.168.1.41:5000
echo.
echo Press Ctrl+C to stop the server
echo ==========================================

venv\Scripts\python.exe run.py

pause
