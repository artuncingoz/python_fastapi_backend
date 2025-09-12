#!/bin/sh
set -e

echo "Waiting for Postgres at: $DATABASE_URL"
# Wait up to 60s for DB to accept connections
python - <<'PY'
import os, sys, time
from sqlalchemy import create_engine
url = os.environ["DATABASE_URL"]
for i in range(60):
    try:
        create_engine(url, pool_pre_ping=True).connect().close()
        print("DB is up"); sys.exit(0)
    except Exception as e:
        time.sleep(1)
print("DB not ready after 60s"); sys.exit(1)
PY

echo "Running Alembic migrations..."
alembic upgrade head

echo "Seeding database (idempotent)..."
python -m app.seed

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
