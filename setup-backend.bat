@echo off
echo ========================================
echo  Backend Setup - Unified GovTech
echo ========================================
echo.

cd backend

echo [1/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create virtual environment
    echo Please ensure Python 3.9+ is installed
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo [3/4] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Downloading spaCy language model...
python -m spacy download en_core_web_sm
if %errorlevel% neq 0 (
    echo [WARNING] Failed to download spaCy model
    echo You may need to download it manually later
)

echo.
echo ========================================
echo  Backend Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run start-backend.bat to start the server
echo.
pause
