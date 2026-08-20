#!/bin/bash

# GovTech Build Script - Creates binaries for both frontend and backend
# Usage: ./build-all.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${PROJECT_ROOT}/dist/release"
FRONTEND_BUILD_DIR="${BUILD_DIR}/frontend"
BACKEND_BUILD_DIR="${BUILD_DIR}/backend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="govtech_ragbot_${TIMESTAMP}"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}║   GovTech RAGBot Build System                  ║${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create directory structure
setup_build_dirs() {
    print_info "Setting up build directories..."
    rm -rf "${BUILD_DIR}"
    mkdir -p "${FRONTEND_BUILD_DIR}"
    mkdir -p "${BACKEND_BUILD_DIR}"
    print_success "Build directories created"
}

# Function to build frontend
build_frontend() {
    print_info "Building frontend..."

    cd "${PROJECT_ROOT}/frontend"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules not found. Installing dependencies..."
        npm install
    fi

    # Build frontend
    print_info "Running Vite build..."
    npm run build

    # Copy built files
    if [ -d "dist" ]; then
        cp -r dist/* "${FRONTEND_BUILD_DIR}/"
        print_success "Frontend built successfully"
    else
        print_error "Frontend build failed - dist directory not found"
        exit 1
    fi

    cd "${PROJECT_ROOT}"
}

# Function to build backend
build_backend() {
    print_info "Building backend..."

    cd "${PROJECT_ROOT}/backend"

    # Use portable venv approach (faster and more reliable than PyInstaller)
    print_info "Creating portable Python environment with Python 3.12..."

    # Remove old venv if it exists
    if [ -d ".venv" ]; then
        print_warning "Removing existing virtual environment..."
        rm -rf .venv
    fi

    # Create virtual environment with Python 3.12 using uv
    print_info "Creating virtual environment with Python 3.12..."
    uv venv .venv --python 3.12

    # Activate virtual environment
    source .venv/bin/activate

    # Verify Python version
    PYTHON_VERSION=$(python --version)
    print_info "Virtual environment Python: ${PYTHON_VERSION}"

    # Install requirements with progress
    print_info "Installing backend dependencies (this will show progress)..."
    uv pip install -r requirements.txt

    print_success "Dependencies installed successfully"

    # Create portable package
    print_info "Creating portable backend package..."

    # Copy virtual environment
    print_info "  [1/4] Copying virtual environment..."
    cp -r .venv "${BACKEND_BUILD_DIR}/venv"

    # Copy source code
    print_info "  [2/4] Copying source code..."
    cp main.py "${BACKEND_BUILD_DIR}/"

    # Copy resources
    print_info "  [3/4] Copying resources..."
    [ -d "legal" ] && cp -r legal "${BACKEND_BUILD_DIR}/"
    [ -f "requirements.txt" ] && cp requirements.txt "${BACKEND_BUILD_DIR}/"
    [ -f "../.env.example" ] && cp ../.env.example "${BACKEND_BUILD_DIR}/.env"

    # Create executable wrapper
    print_info "  [4/4] Creating executable wrapper..."
    cat > "${BACKEND_BUILD_DIR}/govtech_backend" << 'WRAPPER_EOF'
#!/bin/bash
# GovTech Backend Startup Script
set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file with your configuration"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Activate virtual environment
source venv/bin/activate

# Run uvicorn server
echo "Starting GovTech Backend..."
echo "Host: ${HOST:-127.0.0.1}"
echo "Port: ${PORT:-8000}"
echo ""

exec uvicorn main:app \
    --host "${HOST:-127.0.0.1}" \
    --port "${PORT:-8000}" \
    --workers "${WORKERS:-4}" \
    --log-level "${LOG_LEVEL:-info}"
WRAPPER_EOF

    chmod +x "${BACKEND_BUILD_DIR}/govtech_backend"

    # Calculate size
    PACKAGE_SIZE=$(du -sh "${BACKEND_BUILD_DIR}" | cut -f1)
    print_success "Backend package created successfully (${PACKAGE_SIZE})"

    deactivate
    cd "${PROJECT_ROOT}"
}

# Function to create startup scripts
create_startup_scripts() {
    print_info "Creating startup scripts..."

    # Backend startup script
    cat > "${BACKEND_BUILD_DIR}/start_backend.sh" << 'EOF'
#!/bin/bash
# Backend startup script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Please create one from .env.example"
    echo "Press Enter to continue anyway or Ctrl+C to exit..."
    read
fi

# Run the backend binary
echo "Starting GovTech Backend..."
./govtech_backend
EOF
    chmod +x "${BACKEND_BUILD_DIR}/start_backend.sh"

    # Frontend startup script (using Python HTTP server)
    cat > "${FRONTEND_BUILD_DIR}/start_frontend.sh" << 'EOF'
#!/bin/bash
# Frontend startup script

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${1:-3000}

echo "Starting GovTech Frontend on port $PORT..."
echo "Open http://localhost:$PORT in your browser"
echo "Press Ctrl+C to stop the server"

python3 -m http.server $PORT
EOF
    chmod +x "${FRONTEND_BUILD_DIR}/start_frontend.sh"

    # Master startup script
    cat > "${BUILD_DIR}/start_all.sh" << 'EOF'
#!/bin/bash
# Master startup script for both frontend and backend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
echo "Starting Backend..."
cd "$SCRIPT_DIR/backend"
./start_backend.sh &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "Starting Frontend..."
cd "$SCRIPT_DIR/frontend"
./start_frontend.sh 3000 &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "GovTech RAGBot is running!"
echo "=========================================="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Wait for processes
wait
EOF
    chmod +x "${BUILD_DIR}/start_all.sh"

    print_success "Startup scripts created"
}

# Function to create README
create_readme() {
    print_info "Creating README..."

    cat > "${BUILD_DIR}/README.md" << EOF
# GovTech RAGBot - Binary Distribution

Built on: $(date)

## Contents

- **frontend/**: Built React application
- **backend/**: Python backend binary and resources
- **start_all.sh**: Start both frontend and backend

## Quick Start

1. Configure the backend:
   \`\`\`bash
   cd backend
   cp .env .env.local  # Edit with your configuration
   \`\`\`

2. Start the application:
   \`\`\`bash
   ./start_all.sh
   \`\`\`

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000

## Individual Services

### Backend Only
\`\`\`bash
cd backend
./start_backend.sh
\`\`\`

### Frontend Only
\`\`\`bash
cd frontend
./start_frontend.sh [port]  # Default port: 3000
\`\`\`

## Requirements

- Python 3.8+ (for HTTP server and backend binary)
- Modern web browser
- Linux/Unix environment

## Configuration

Edit \`backend/.env\` file with your:
- Google API keys
- Database credentials
- Other environment variables

## Support

For issues or questions, refer to the original source repository.
EOF

    print_success "README created"
}

# Function to create archive
create_archive() {
    print_warning "Skipping archive creation (7.5GB+ would take too long)"
    print_info "Use rsync to deploy: rsync -avz dist/release/ user@server:/opt/govtech-ragbot/"
    print_info ""
    print_info "Or create archive manually later:"
    print_info "  cd dist && tar -czf ${ARCHIVE_NAME}.tar.gz release/"

    # Optionally create a deployment info file
    cat > "${BUILD_DIR}/DEPLOY.txt" << EOF
Deployment built on: $(date)
Build directory: ${BUILD_DIR}
Size: $(du -sh ${BUILD_DIR} | cut -f1)

Quick Deploy:
  rsync -avz ${BUILD_DIR}/ user@server:/opt/govtech-ragbot/

Manual Archive (optional):
  cd ${PROJECT_ROOT}/dist
  tar -czf ${ARCHIVE_NAME}.tar.gz release/
EOF

    print_success "Build complete! Archive creation skipped for speed."
}

# Function to show build summary
show_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}║   Build Completed Successfully!                ║${NC}"
    echo -e "${GREEN}║                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    print_info "Build artifacts location:"
    echo "  Directory: ${BUILD_DIR}"
    echo ""
    print_info "Build size:"
    du -sh "${BUILD_DIR}"
    echo ""
    print_info "To deploy (use rsync - fastest):"
    echo "  rsync -avz --progress ${BUILD_DIR}/ user@server:/opt/govtech-ragbot/"
    echo ""
    print_info "Or see DEPLOY.txt for instructions:"
    echo "  cat ${BUILD_DIR}/DEPLOY.txt"
    echo ""
}

# Main build process
main() {
    print_header

    # Check prerequisites
    print_info "Checking prerequisites..."

    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js first."
        exit 1
    fi

    if ! command_exists uv; then
        print_error "uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # uv will automatically download Python 3.12 if not available
    print_info "uv will automatically download Python 3.12 if needed"

    print_success "Prerequisites check passed"

    # Execute build steps
    setup_build_dirs
    build_frontend
    build_backend
    create_startup_scripts
    create_readme
    create_archive
    show_summary
}

# Run main function
main
