@echo off
REM DataInsights AI - Quick Start Script for Windows

echo 🚀 DataInsights AI - Quick Start
echo ================================

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop first.
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found. Please install Docker Desktop first.
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Check for .env file
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your OPENAI_API_KEY
    echo Press Enter after adding your API key...
    pause
)

REM Start services
echo Starting DataInsights AI services...
docker-compose up -d

echo.
echo ✅ DataInsights AI is starting up!
echo.
echo Services:
echo   - Frontend: http://localhost:3000
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/api/docs
echo.
echo View logs:
echo   docker-compose logs -f
echo.
echo Stop services:
echo   docker-compose down
echo.

pause
