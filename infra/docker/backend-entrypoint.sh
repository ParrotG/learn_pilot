#!/usr/bin/env bash
set -euo pipefail

cd /app/backend

mkdir -p data/uploads data/exports

echo "[backend-entrypoint] Applying database migrations..."
./.venv/bin/alembic upgrade head

echo "[backend-entrypoint] Starting FastAPI service..."
exec ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
