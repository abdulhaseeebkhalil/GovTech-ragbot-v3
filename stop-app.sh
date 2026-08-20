#!/bin/bash

echo "========================================"
echo " Unified GovTech - Stopping Application"
echo "========================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if PID files exist
if [ -f "$SCRIPT_DIR/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/logs/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "Backend stopped."
    else
        echo "Backend process not running."
    fi
    rm "$SCRIPT_DIR/logs/backend.pid"
else
    echo "No backend PID file found."
fi

if [ -f "$SCRIPT_DIR/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/logs/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "Frontend stopped."
    else
        echo "Frontend process not running."
    fi
    rm "$SCRIPT_DIR/logs/frontend.pid"
else
    echo "No frontend PID file found."
fi

# Also kill any orphaned processes just to be safe
echo ""
echo "Cleaning up any orphaned processes..."
pkill -f "uvicorn main:app" 2>/dev/null && echo "Killed uvicorn processes" || echo "No uvicorn processes found"
pkill -f "vite" 2>/dev/null && echo "Killed vite processes" || echo "No vite processes found"

echo ""
echo "========================================"
echo " Application Stopped"
echo "========================================"
echo ""
