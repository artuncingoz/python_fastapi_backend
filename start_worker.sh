#!/bin/sh
set -e

echo "Waiting for Postgres at: $DATABASE_URL"
python - <<'PY'
import os, sys, time
from sqlalchemy import create_engine
url = os.environ["DATABASE_URL"]
for i in range(60):
    try:
        create_engine(url, pool_pre_ping=True).connect().close()
        print("DB is up"); sys.exit(0)
    except Exception as e:
        print(f"DB not ready (attempt {i+1}/60): {e}")
        time.sleep(1)
print("DB not ready after 60s"); sys.exit(1)
PY

echo "Starting RQ worker..."
exec rq worker --url "${REDIS_URL}" "${RQ_QUEUE_NAME}"
