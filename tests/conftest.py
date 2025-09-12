# tests/conftest.py
import os
import sys
import pathlib
import pytest
import fakeredis

# Ensure project root (folder that contains "app/") is importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Test env defaults
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app
from app.deps import get_redis
from app.db.base import Base
from app.db.session import engine

@pytest.fixture(scope="session", autouse=True)
def _create_db():
    # Create all tables on the test engine
    Base.metadata.create_all(bind=engine)
    yield
    # Optionally drop after tests
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def _override_redis():
    # Use real in-memory Redis with pipeline support so RQ enqueue works
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: fake
    yield
    app.dependency_overrides.pop(get_redis, None)
