#!/bin/bash
# Vertex AI Platform — Development Startup Script

set -e

echo "🚀 Starting Vertex AI Platform (Development Mode)"
echo "================================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required. Install from python.org"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required. Install from nodejs.org"; exit 1; }

# Setup Backend
echo ""
echo "📦 Setting up Backend..."
cd "$(dirname "$0")/../backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Created virtual environment"
fi

source venv/bin/activate
pip install -r requirements.txt --quiet

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example — please update with your API keys"
fi

echo "✅ Backend ready"

# Setup Frontend
echo ""
echo "📦 Setting up Frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    npm install
fi

echo "✅ Frontend ready"

# Start services
echo ""
echo "🟢 Starting services..."
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Frontend: http://localhost:3000"
echo ""

# Start backend in background
cd ../backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend in background
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "Press Ctrl+C to stop all services"

# Trap SIGINT
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
