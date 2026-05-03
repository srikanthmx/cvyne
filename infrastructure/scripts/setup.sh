#!/usr/bin/env bash
# AutoApply AI — full local dev setup
set -euo pipefail

echo "🚀 AutoApply AI — Dev Setup"
echo "=============================="

# Prerequisites check
command -v docker >/dev/null 2>&1 || { echo "❌ Docker required"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "❌ pnpm required (npm i -g pnpm)"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "❌ uv required (curl -LsSf https://astral.sh/uv/install.sh | sh)"; exit 1; }
command -v python3.12 >/dev/null 2>&1 || python3 --version | grep -q "3.12" || { echo "❌ Python 3.12 required"; exit 1; }

echo "✓ Prerequisites OK"

# Copy env example
if [ ! -f apps/api/.env ]; then
  cp .env.example apps/api/.env
  echo "📝 Created apps/api/.env — fill in secrets before running"
fi

# Start infrastructure
echo "🐳 Starting Docker services (postgres, redis, minio)..."
docker compose -f infrastructure/docker/docker-compose.yml up -d --wait
echo "✓ Postgres, Redis, MinIO running"

echo ""
echo "ℹ️  open-design daemon is opt-in (heavier build):"
echo "    docker compose -f infrastructure/docker/docker-compose.yml --profile full up -d open-design"
echo "    Then verify: curl http://localhost:4477/api/design-systems"
echo ""

# Node dependencies
echo "📦 Installing Node dependencies..."
pnpm install

# Python dependencies
echo "🐍 Installing Python dependencies..."
(cd apps/api && uv sync)

# Playwright browsers for browser-use
echo "🌐 Installing Playwright Chromium for browser-use..."
(cd apps/api && uv run playwright install chromium) 2>/dev/null || echo "⚠️  Playwright install skipped"

# Database migration
echo "🗄️  Running database migrations..."
(cd apps/api && uv run alembic upgrade head) 2>/dev/null || echo "⚠️  Migrations skipped (alembic not configured yet — Kiro's task)"

# MinIO bucket
echo "🪣  Setting up MinIO bucket..."
docker run --rm --network host minio/mc:latest \
  sh -c "mc alias set local http://localhost:9000 minioadmin minioadmin && mc mb --ignore-existing local/cvyne" \
  2>/dev/null || echo "⚠️  MinIO bucket setup skipped"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Start dev servers:"
echo "  pnpm dev           # Next.js frontend"
echo "  cd apps/api && make dev  # FastAPI backend"
echo "  cd apps/api && make worker  # Celery worker"
