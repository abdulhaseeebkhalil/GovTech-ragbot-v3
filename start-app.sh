#!/bin/bash

echo "========================================"
echo " Unified GovTech - Starting Application"
echo "========================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if backend virtual environment exists
if [ ! -d "$SCRIPT_DIR/backend/venv" ]; then
    echo "[ERROR] Backend not set up!"
    echo "Please set up backend first:"
    echo "  cd backend"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "[ERROR] Frontend not set up!"
    echo "Please set up frontend first:"
    echo "  cd frontend"
    echo "  npm install"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo "[1/2] Starting Backend Server..."
echo ""

# Start backend in background (localhost only - accessible via port 5173 proxy)
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
nohup python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 > "$SCRIPT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$SCRIPT_DIR/logs/backend.pid"
echo "Backend started with PID: $BACKEND_PID (internal only)"

echo "Waiting 5 seconds for backend to initialize..."
sleep 5

echo ""
echo "[2/2] Starting Frontend Server..."
echo ""

# Start frontend in background
cd "$SCRIPT_DIR/frontend"
nohup npm run dev > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$SCRIPT_DIR/logs/frontend.pid"
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "========================================"
echo " Application Started Successfully!"
echo "========================================"
echo ""
echo "🌐 Access Application at: http://localhost:5173"
echo ""
echo "Services running:"
echo "  ✅ Frontend + Backend APIs (Port 5173)"
echo "     - Chat: http://localhost:5173/chat"
echo "     - Legal: http://localhost:5173/legal/analyze"
echo "     - Health: http://localhost:5173/health"
echo ""
echo "  🔒 Backend (Port 8000 - Internal Only)"
echo "     - Not accessible externally"
echo "     - Proxied through port 5173"
echo ""
echo "Logs:"
echo "  - Backend:  $SCRIPT_DIR/logs/backend.log"
echo "  - Frontend: $SCRIPT_DIR/logs/frontend.log"
echo ""
echo "To view logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo ""
echo "To stop the application:"
echo "  ./stop-app.sh"
echo "  Or manually: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Application is running!"
echo "Open http://localhost:5173 in your browser"
echo ""

# Cleanup function for systemd
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap signals for systemd
trap cleanup SIGTERM SIGINT

# Wait for processes (keeps script running for systemd)
wait
