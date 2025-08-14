@echo off
REM start-dev.bat - Windows Development Startup Script
REM ================================================
REM 
REM Starts both frontend and backend for SLATE development
REM Frontend: React + Vite on port 5173  
REM Backend: FastAPI on port 8000

echo 🚀 Starting SLATE Development Environment
echo ========================================

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Error: package.json not found. Please run this script from the slate directory.
    pause
    exit /b 1
)

REM Start backend in background
echo 🔧 Starting backend server...
start /b cmd /c "cd backend && python simple_backend.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo 🎨 Starting frontend development server...
start /b cmd /c "npm run dev"

REM Print information
echo.
echo ✅ SLATE Development Environment Started!
echo ========================================
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend:  http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop servers and exit...
echo.

pause > nul

REM Kill background processes (this is basic, in production you'd want better process management)
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul

echo 🛑 Servers stopped.
pause
