#!/usr/bin/env sh
set -e

echo "==> Running database migrations (alembic upgrade head)..."
alembic upgrade head

echo "==> Seeding initial demo data..."
python -m app.seed.init_demo_data

echo "==> Starting Uvicorn API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
