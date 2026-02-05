@echo off
echo ========================================
echo AlgoInsight Backend Server with Live Logs
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: Virtual environment not found at .venv\
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Starting server...
echo Logs will be saved to: logs\algoinsight_*.log
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
