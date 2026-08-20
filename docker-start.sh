#!/bin/bash
# Docker Quick Start Script - Jira Agentic Development System

echo "=========================================="
echo "  Jira Agentic Development System"
echo "  Docker Quick Start"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please copy .env.docker to .env and configure it"
    echo ""
    echo "   cp .env.docker .env"
    echo "   # Then edit .env with your credentials"
    exit 1
fi

echo "✅ Environment file found"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Build and start containers
echo "🐳 Building and starting containers..."
echo ""

docker-compose up --build -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Wait for backend
echo "   Checking backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ⚠️  Backend health check timeout"
    fi
    sleep 2
done

# Wait for frontend
echo "   Checking frontend..."
for i in {1..15}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "   ✅ Frontend is healthy"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "   ⚠️  Frontend health check timeout"
    fi
    sleep 2
done

# Wait for vectordb
echo "   Checking vector database..."
for i in {1..20}; do
    if curl -s http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
        echo "   ✅ Vector database is healthy"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "   ⚠️  Vector database health check timeout"
    fi
    sleep 2
done

echo ""
echo "=========================================="
echo "  🎉 System is ready!"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   VectorDB:  http://localhost:8001"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop system:   docker-compose down"
echo "   Restart:       docker-compose restart"
echo ""
echo "🚀 Ready for demo!"
echo ""
