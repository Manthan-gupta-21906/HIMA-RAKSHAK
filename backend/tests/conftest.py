"""Pytest session bootstrap and shared isolated database fixtures."""

import os
import secrets
from collections.abc import Generator
from pathlib import Path

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("JWT_SECRET_KEY", secrets.token_urlsafe(32))

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.db.session import create_db_engine, get_session_factory  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """Provide an isolated, migrated SQLAlchemy Session per test with rollback and cleanup."""
    db_url = f"sqlite:///{tmp_path / 'integration_test.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        engine.dispose()
