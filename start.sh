#!/bin/bash
# CodeJudge - Quick Setup Script
set -e

echo "╔══════════════════════════════════╗"
echo "║     CodeJudge Setup Script       ║"
echo "╚══════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &>/dev/null; then
  echo "❌ Docker not found. Install Docker first: https://docs.docker.com/get-docker/"
  exit 1
fi

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
  echo "❌ Docker Compose not found."
  exit 1
fi

echo "✅ Docker found"
echo ""
echo "🚀 Starting CodeJudge..."
echo ""

# Use 'docker compose' (v2) or 'docker-compose' (v1)
if docker compose version &>/dev/null 2>&1; then
  DC="docker compose"
else
  DC="docker-compose"
fi

$DC down --remove-orphans 2>/dev/null || true
$DC up --build -d

echo ""
echo "⏳ Waiting for services..."
sleep 8

echo ""
echo "╔══════════════════════════════════╗"
echo "║     CodeJudge is running! 🎉     ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "  🌐 Frontend:  http://localhost:3000"
echo "  🔧 Backend:   http://localhost:5000"
echo "  🗄️  MySQL:     localhost:3306"
echo ""
echo "  Default DB password: codejudge123"
echo ""
echo "  To stop: docker compose down"
echo "  To view logs: docker compose logs -f"
echo ""
