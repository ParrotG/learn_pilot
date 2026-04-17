#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BACKEND_ENV="$PROJECT_ROOT/backend/.env"
FRONTEND_ENV="$PROJECT_ROOT/frontend/.env.local"

if [[ ! -f "$BACKEND_ENV" ]]; then
  echo "Missing backend environment file: $BACKEND_ENV"
  echo "Create it from backend/.env.example before starting Docker services."
  exit 1
fi

if [[ ! -f "$FRONTEND_ENV" ]]; then
  echo "Missing frontend environment file: $FRONTEND_ENV"
  echo "Create it from frontend/.env.example before starting Docker services."
  exit 1
fi

mkdir -p "$PROJECT_ROOT/backend/data/uploads" "$PROJECT_ROOT/backend/data/exports"

docker compose -f "$SCRIPT_DIR/docker-compose.yml" up --build -d "$@"
