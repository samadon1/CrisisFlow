#!/bin/bash

# CrisisFlow Local Development Startup Script
# Starts all components for local development

set -e

echo "🚨 CrisisFlow Local Development"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and add your API keys"
    exit 1
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Warning: Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to wait for service
wait_for_service() {
    echo "Waiting for $1 to be ready..."
    while ! curl -s http://localhost:$2/api/health > /dev/null 2>&1; do
        sleep 2
    done
    echo -e "${GREEN}✅ $1 is ready!${NC}"
}

# Kill existing processes on our ports
cleanup() {
    echo "Cleaning up existing processes..."
    pkill -f "weather_producer.py" 2>/dev/null || true
    pkill -f "social_producer.py" 2>/dev/null || true
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    sleep 2
}

# Trap to cleanup on exit
trap cleanup EXIT

# Check ports
echo "Checking ports..."
check_port 8000 || { echo "Please stop the service on port 8000"; exit 1; }
check_port 5173 || { echo "Please stop the service on port 5173"; exit 1; }

# Start Backend
start_backend() {
    echo -e "${GREEN}Starting Backend API...${NC}"
    cd backend
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    uvicorn main:app --reload --port 8000 &
    BACKEND_PID=$!
    cd ..
    sleep 5
}

# Start Producers
start_producers() {
    echo -e "${GREEN}Starting Weather Producer...${NC}"
    cd producers
    if [ ! -d "venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi

    python weather_producer.py &
    WEATHER_PID=$!

    echo -e "${GREEN}Starting Social Producer...${NC}"
    python social_producer.py &
    SOCIAL_PID=$!

    cd ..
}

# Start Frontend
start_frontend() {
    echo -e "${GREEN}Starting Frontend...${NC}"
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing npm packages..."
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ..
}

# Main execution
main() {
    echo "Starting CrisisFlow components..."
    echo ""

    # Optional: cleanup old processes
    cleanup

    # Start all services
    start_backend
    wait_for_service "Backend API" 8000

    start_producers
    echo -e "${GREEN}✅ Producers started${NC}"

    start_frontend
    sleep 5
    echo -e "${GREEN}✅ Frontend started${NC}"

    echo ""
    echo "======================================="
    echo -e "${GREEN}🎉 CrisisFlow is running!${NC}"
    echo "======================================="
    echo ""
    echo "📍 Frontend: http://localhost:5173"
    echo "📍 Backend API: http://localhost:8000"
    echo "📍 API Docs: http://localhost:8000/api/docs"
    echo ""
    echo "Logs are displayed above. Press Ctrl+C to stop all services."
    echo ""

    # Keep script running
    wait
}

# Run main
main