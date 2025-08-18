@echo off
echo 🚀 Starting SLATE - Frontend and Backend
echo ========================================

echo 🔧 Starting backend server...
start /b cmd /c "cd backend && python main.py"

echo ⏳ Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo 🎨 Starting frontend development server...
start cmd /c "npm run dev"

echo.
echo ✅ SLATE Development Environment Started!
echo ========================================
echo 🌐 Frontend: http://localhost:5173
echo 🔧 Backend:  http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop servers and exit...
pause > nul

echo 🛑 Stopping servers...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul
echo Servers stopped.
