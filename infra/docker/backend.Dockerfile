FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl pandoc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml backend/uv.lock backend/alembic.ini ./
RUN uv sync --frozen --no-dev

COPY backend /app/backend
COPY infra/docker/backend-entrypoint.sh /app/backend-entrypoint.sh

RUN chmod +x /app/backend-entrypoint.sh \
    && mkdir -p /app/backend/data/uploads /app/backend/data/exports

EXPOSE 8000

ENTRYPOINT ["/app/backend-entrypoint.sh"]
