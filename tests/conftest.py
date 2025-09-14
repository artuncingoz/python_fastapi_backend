# tests/conftest.py
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Test env: in-memory SQLite, dummy Redis URL (not actually used)
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SUMMARIZER_BACKEND", "rule")  # keep tests fast & deterministic

import pytest
import fakeredis

from app.main import app
from app.deps import get_redis
from app.db.base import Base
from app.db.session import engine, SessionLocal

def _fake_redis():
    return fakeredis.FakeStrictRedis(decode_responses=True)

@pytest.fixture(autouse=True, scope="session")
def _create_schema_once():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def _db_session_clean():
    yield

@pytest.fixture(autouse=True)
def _override_redis_dep():
    app.dependency_overrides[get_redis] = _fake_redis
    yield
    app.dependency_overrides.pop(get_redis, None)
