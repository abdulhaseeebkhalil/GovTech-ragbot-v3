@echo off
echo ========================================
echo  Unified GovTech - Starting Application
echo ========================================
echo.

REM Check if backend virtual environment exists
if not exist "backend\venv\" (
    echo [ERROR] Backend not set up!
    echo Please run setup-backend.bat first
    pause
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "frontend\node_modules\" (
    echo [ERROR] Frontend not set up!
    echo Please run setup-frontend.bat first
    pause
    exit /b 1
)

echo [1/2] Starting Backend Server...
echo.
start "GovTech Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak > nul

echo.
echo [2/2] Starting Frontend Server...
echo.
start "GovTech Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo  Application Started Successfully!
echo ========================================
echo.
echo Two windows have been opened:
echo   1. GovTech Backend  (http://localhost:8000)
echo   2. GovTech Frontend (http://localhost:5173)
echo.
echo Wait for both to fully start, then open:
echo   http://localhost:5173
echo.
echo To stop the application:
echo   Close both terminal windows (Backend and Frontend)
echo.
echo Press any key to open browser...
pause > nul

start http://localhost:5173

echo.
echo Application is running!
echo Close this window when done.
echo.
