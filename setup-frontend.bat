@echo off
echo ========================================
echo  Frontend Setup - Unified GovTech
echo ========================================
echo.

cd frontend

echo [1/1] Installing Node dependencies...
npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    echo Please ensure Node.js 18+ is installed
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Frontend Setup Complete!
echo ========================================
echo.
echo Next step:
echo Run start-frontend.bat to start the dev server
echo.
pause
