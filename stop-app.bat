@echo off
echo ========================================
echo  Unified GovTech - Stopping Application
echo ========================================
echo.

echo Stopping Backend Server (port 8000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /PID %%a /F 2>nul

echo Stopping Frontend Server (port 5173)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /PID %%a /F 2>nul

echo.
echo ========================================
echo  Application Stopped
echo ========================================
echo.
pause
