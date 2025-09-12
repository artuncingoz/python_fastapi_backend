#!/usr/bin/env bash
# bootstrap-compose.sh
set -euo pipefail

info(){ printf "\033[1;36m==> %s\033[0m\n" "$*"; }

# 0) Check Docker
info "Checking Docker..."
docker version >/dev/null

# 1) Ensure .env exists
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    info "Creating .env from .env.example"
    cp .env.example .env
  else
    echo "ERROR: .env not found and .env.example missing. Create a .env first." >&2
    exit 1
  fi
fi

# 2) Fresh start (remove old containers; keep volumes)
info "Stopping previous stack (if any)..."
docker compose down --remove-orphans

# 3) Build
info "Building images..."
docker compose build

# 4) Up
info "Starting stack..."
docker compose up -d

# 5) Wait for health
HEALTH_URL="http://localhost:8000/health"
TRIES=60
until curl -fsS "$HEALTH_URL" >/dev/null || [[ $TRIES -le 0 ]]; do
  TRIES=$((TRIES-1))
  sleep 2
done

if ! curl -fsS "$HEALTH_URL" >/dev/null; then
  echo "WARN: API did not become healthy. Recent logs:" >&2
  docker compose logs --tail=200 api || true
  exit 1
fi

info "API is healthy at $HEALTH_URL"
info "Open Swagger: http://localhost:8000/docs"

echo "Done. Follow logs with:"
echo "  docker compose logs -f api"
echo "  docker compose logs -f worker"
