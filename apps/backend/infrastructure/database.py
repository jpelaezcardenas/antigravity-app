from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

Base = declarative_base()

_engine = None
_SessionLocal = None


def _init_engine():
    """Create the engine/session factory lazily on first use.

    Avoids constructing an engine at import time (which fails when DATABASE_URL
    is unset, e.g. in environments that only use Supabase).
    """
    global _engine, _SessionLocal
    if _engine is None:
        if not SQLALCHEMY_DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured; cannot create a database engine."
            )
        _engine = create_engine(SQLALCHEMY_DATABASE_URL)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_engine():
    """Return the lazily-initialized SQLAlchemy engine."""
    _init_engine()
    return _engine


def get_db():
    _init_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
