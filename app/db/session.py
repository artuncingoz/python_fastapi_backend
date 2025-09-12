# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import make_url
from app.config import settings

url = make_url(settings.database_url)

engine_kwargs = dict(pool_pre_ping=True, future=True)
connect_args = {}

if url.drivername.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    # keep the same in-memory DB for all connections during tests
    if url.database in (":memory:", ""):
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
