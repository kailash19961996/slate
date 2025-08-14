#!/bin/bash

# start-dev.sh - Development Startup Script
# ========================================
# 
# Starts both frontend and backend for SLATE development
# Frontend: React + Vite on port 5173
# Backend: FastAPI on port 8000

echo "🚀 Starting SLATE Development Environment"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the slate directory."
    exit 1
fi

# Start backend in background
echo "🔧 Starting backend server..."
cd backend
python simple_backend.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🎨 Starting frontend development server..."
npm run dev &
FRONTEND_PID=$!

# Print information
echo ""
echo "✅ SLATE Development Environment Started!"
echo "========================================"
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for user to stop
trap "echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
