"""Database engine, session factory, and rollback-safe session dependency."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def create_db_engine(database_url: str | None = None) -> Engine:
    """Create a SQLAlchemy engine for PostgreSQL/PostGIS or SQLite."""
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Build a configured sessionmaker."""
    bound_engine = engine or create_db_engine()
    return sessionmaker(bind=bound_engine, autoflush=False, autocommit=False)


def get_db(
    session_factory: sessionmaker[Session] | None = None,
) -> Generator[Session, None, None]:
    """Yield a database session with automatic commit, rollback on error, and close."""
    factory = session_factory or get_session_factory()
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
