#!/usr/bin/env bash
# ============================================================================
# AutoApply AI — Single Runner
# Starts: docker services + FastAPI + Celery worker + Celery beat + Next.js
# Stops: all of them cleanly on Ctrl+C
#
# Usage:
#   ./run.sh                  # start everything
#   ./run.sh --no-design      # skip the open-design sidecar (saves resources)
#   ./run.sh --no-beat        # skip Celery beat (no scheduled retries)
#   ./run.sh --setup          # run first-time setup (deps + migrations) then start
#   ./run.sh --infra-only     # only start docker services, then exit
#   ./run.sh --stop           # stop all docker services and exit
# ============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Colors for prefixed log output
C_RESET='\033[0m'
C_INFRA='\033[0;36m'    # cyan
C_API='\033[0;32m'       # green
C_WORKER='\033[0;33m'    # yellow
C_BEAT='\033[0;35m'      # magenta
C_WEB='\033[0;34m'       # blue
C_BOLD='\033[1m'

WITH_DESIGN=true
WITH_BEAT=true
DO_SETUP=false
INFRA_ONLY=false
STOP_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --no-design) WITH_DESIGN=false ;;
    --no-beat) WITH_BEAT=false ;;
    --setup) DO_SETUP=true ;;
    --infra-only) INFRA_ONLY=true ;;
    --stop) STOP_ONLY=true ;;
    -h|--help)
      sed -n '1,20p' "$0"; exit 0 ;;
  esac
done

# ────────────────────────────── prerequisite checks ─────────────────────────
need() { command -v "$1" >/dev/null 2>&1 || { echo "❌ Missing: $1"; echo "   See GETTING_STARTED.md for install instructions."; exit 1; }; }
need docker
need pnpm
need uv
need python3

# Verify .env exists; if not, offer to create from example
if [ ! -f apps/api/.env ]; then
  echo "⚠️  apps/api/.env not found."
  if [ -f .env.example ]; then
    read -p "Create apps/api/.env from .env.example now? [y/N] " ans
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      cp .env.example apps/api/.env
      # Auto-generate keys
      ENC_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
      SEC_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
      # macOS sed needs '' after -i; GNU sed doesn't — use a portable workaround
      python3 -c "
import pathlib, re
p = pathlib.Path('apps/api/.env')
t = p.read_text()
t = re.sub(r'^ENCRYPTION_KEY=.*$', 'ENCRYPTION_KEY=$ENC_KEY', t, flags=re.M)
t = re.sub(r'^SECRET_KEY=.*$', 'SECRET_KEY=$SEC_KEY', t, flags=re.M)
p.write_text(t)
"
      echo "✓ Generated ENCRYPTION_KEY and SECRET_KEY in apps/api/.env"
      echo "→ You still need to fill in CLERK_SECRET_KEY and (optional) LANGFUSE_*"
      echo "→ See GETTING_STARTED.md § Environment Variables"
      exit 0
    fi
  fi
  echo "Run: cp .env.example apps/api/.env && edit it"; exit 1
fi

if [ ! -f apps/web/.env.local ]; then
  echo "⚠️  apps/web/.env.local not found. Create it with at minimum:"
  echo "   NEXT_PUBLIC_API_URL=http://localhost:8000"
  echo "   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_..."
  echo "   CLERK_SECRET_KEY=sk_test_..."
  exit 1
fi

# ────────────────────────────── stop-only mode ──────────────────────────────
if $STOP_ONLY; then
  echo "🛑 Stopping all docker services..."
  docker compose -f infrastructure/docker/docker-compose.yml --profile full down
  echo "✓ Stopped"
  exit 0
fi

# ────────────────────────────── setup mode ──────────────────────────────────
if $DO_SETUP; then
  echo -e "${C_BOLD}📦 Installing dependencies...${C_RESET}"
  pnpm install
  (cd apps/api && uv sync)
  (cd apps/api && uv run playwright install chromium) || echo "⚠️  Playwright install failed (browser-use will not work)"
  echo -e "${C_BOLD}🗄️  Running database migrations...${C_RESET}"
  (cd apps/api && uv run alembic upgrade head) || echo "⚠️  Migrations failed — DB may not be running yet"
  echo "✓ Setup complete"
fi

# ────────────────────────────── start docker infra ──────────────────────────
echo -e "${C_INFRA}[infra]${C_RESET} Starting Postgres, Redis, MinIO, Flower..."
COMPOSE="docker compose -f infrastructure/docker/docker-compose.yml"
PROFILE_ARGS=""
if $WITH_DESIGN; then
  PROFILE_ARGS="--profile full"
  echo -e "${C_INFRA}[infra]${C_RESET} Including open-design sidecar (slower first build)"
fi

$COMPOSE $PROFILE_ARGS up -d --wait postgres redis minio flower
if $WITH_DESIGN; then
  $COMPOSE $PROFILE_ARGS up -d open-design || echo -e "${C_INFRA}[infra]${C_RESET} ⚠️  open-design failed to start (continuing — fallback PDF will be used)"
fi
echo -e "${C_INFRA}[infra]${C_RESET} ✓ ready"

if $INFRA_ONLY; then
  echo "Infra-only mode — exiting. Use './run.sh --stop' to tear down."
  exit 0
fi

# Run migrations once at startup (safe — alembic upgrade head is idempotent)
echo -e "${C_API}[api]${C_RESET} Running migrations..."
(cd apps/api && uv run alembic upgrade head) || echo -e "${C_API}[api]${C_RESET} ⚠️  Migration step failed"

# Verify MinIO bucket exists (idempotent)
docker run --rm --network host minio/mc:latest \
  sh -c "mc alias set local http://localhost:9000 minioadmin minioadmin >/dev/null && mc mb --ignore-existing local/cvyne >/dev/null" \
  2>/dev/null || true

# ────────────────────────────── launch processes ────────────────────────────
LOG_DIR="$ROOT/.run-logs"
mkdir -p "$LOG_DIR"

PIDS=()

start_proc() {
  local name="$1" color="$2" cmd="$3"
  echo -e "${color}[${name}]${C_RESET} starting..."
  bash -c "$cmd" 2>&1 | sed -u "s|^|$(printf "${color}[%-6s]${C_RESET} " "$name")|" &
  PIDS+=($!)
}

cleanup() {
  echo -e "\n${C_BOLD}🛑 Shutting down...${C_RESET}"
  # Send TERM to all child processes and process groups
  for pid in "${PIDS[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  # Give them 3s to exit gracefully
  sleep 3
  for pid in "${PIDS[@]}"; do
    kill -KILL "$pid" 2>/dev/null || true
  done
  echo "✓ Processes stopped (docker services left running — use './run.sh --stop' to remove them)"
  exit 0
}
trap cleanup INT TERM

start_proc "api" "$C_API" "cd apps/api && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000"
start_proc "worker" "$C_WORKER" "cd apps/api && uv run celery -A workers.celery_app worker --loglevel=info --concurrency=2"
if $WITH_BEAT; then
  start_proc "beat" "$C_BEAT" "cd apps/api && uv run celery -A workers.celery_app beat --loglevel=info"
fi
start_proc "web" "$C_WEB" "cd apps/web && pnpm dev"

sleep 2
echo ""
echo -e "${C_BOLD}🚀 AutoApply AI is up:${C_RESET}"
echo "   • Frontend:       http://localhost:3000"
echo "   • API:            http://localhost:8000  (docs: http://localhost:8000/docs)"
echo "   • Celery Flower:  http://localhost:5555"
echo "   • MinIO console:  http://localhost:9001  (minioadmin / minioadmin)"
$WITH_DESIGN && echo "   • open-design:    http://localhost:4477"
echo ""
echo "   Press Ctrl+C to stop. Docker services stay up — './run.sh --stop' removes them."
echo ""

wait
