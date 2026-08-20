@echo off
echo ========================================
echo  Starting Unified GovTech Frontend
echo ========================================
echo.

cd frontend

REM Check if node_modules exists
if not exist "node_modules\" (
    echo [ERROR] Node modules not found!
    echo Please run setup-frontend.bat first
    pause
    exit /b 1
)

echo Starting frontend dev server...
echo.
echo Frontend will be available at:
echo   - Main UI: http://localhost:5173
echo.
echo Press CTRL+C to stop the server
echo.

npm run dev
