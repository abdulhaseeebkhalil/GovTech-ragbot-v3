@echo off
echo ========================================
echo  Starting Unified GovTech Backend
echo ========================================
echo.

cd backend

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup-backend.bat first
    pause
    exit /b 1
)

echo [1/2] Activating virtual environment...
call venv\Scripts\activate

echo [2/2] Starting backend server...
echo.
echo Backend will be available at:
echo   - Main API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000/health
echo.
echo Press CTRL+C to stop the server
echo.

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
