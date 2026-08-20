@echo off
REM Docker Quick Start Script - Jira Agentic Development System (Windows)

echo ==========================================
echo   Jira Agentic Development System
echo   Docker Quick Start
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ❌ Error: .env file not found
    echo    Please copy .env.docker to .env and configure it
    echo.
    echo    copy .env.docker .env
    echo    REM Then edit .env with your credentials
    exit /b 1
)

echo ✅ Environment file found
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker is not running
    echo    Please start Docker Desktop and try again
    exit /b 1
)

echo ✅ Docker is running
echo.

REM Build and start containers
echo 🐳 Building and starting containers...
echo.

docker-compose up --build -d

REM Wait for services to be healthy
echo.
echo ⏳ Waiting for services to be healthy...
echo.

REM Wait for backend
echo    Checking backend...
timeout /t 10 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  Backend starting... (may take a moment)
) else (
    echo    ✅ Backend is healthy
)

REM Wait for frontend
echo    Checking frontend...
timeout /t 5 /nobreak >nul
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  Frontend starting... (may take a moment)
) else (
    echo    ✅ Frontend is healthy
)

REM Wait for vectordb
echo    Checking vector database...
timeout /t 5 /nobreak >nul
curl -s http://localhost:8001/api/v1/heartbeat >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  Vector database starting... (may take a moment)
) else (
    echo    ✅ Vector database is healthy
)

echo.
echo ==========================================
echo   🎉 System is ready!
echo ==========================================
echo.
echo 📊 Service URLs:
echo    Frontend:  http://localhost:3000
echo    Backend:   http://localhost:8000
echo    API Docs:  http://localhost:8000/docs
echo    VectorDB:  http://localhost:8001
echo.
echo 📝 Useful commands:
echo    View logs:     docker-compose logs -f
echo    Stop system:   docker-compose down
echo    Restart:       docker-compose restart
echo.
echo 🚀 Ready for demo!
echo.

pause
