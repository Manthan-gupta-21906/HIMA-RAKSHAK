"""Tests for Alembic migrations, PostGIS SQL, and session rollback/cleanup."""

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect

from alembic import command
from app.db.session import create_db_engine, get_db, get_session_factory
from app.models.source import SourceModel

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _alembic_cfg(db_url: str) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def test_alembic_upgrade_and_downgrade(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'mig.db'}"
    cfg = _alembic_cfg(db_url)

    command.upgrade(cfg, "head")
    engine = create_db_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    assert {"locations", "sources", "alembic_version"}.issubset(tables)

    command.downgrade(cfg, "base")
    tables_after = set(inspect(engine).get_table_names())
    assert "locations" not in tables_after
    assert "sources" not in tables_after
    engine.dispose()


def test_session_rollback_on_error_and_cleanup(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'session.db'}"
    command.upgrade(_alembic_cfg(db_url), "head")
    engine = create_db_engine(db_url)
    factory = get_session_factory(engine)

    gen = get_db(factory)
    db = next(gen)
    db.add(
        SourceModel(
            source_id="src-rollback",
            source_name="Temp",
            source_type="weather",
            licence="MIT",
            update_frequency_minutes=60,
        )
    )
    with pytest.raises(RuntimeError, match="boom"):
        gen.throw(RuntimeError("boom"))

    with factory() as verify_db:
        assert verify_db.get(SourceModel, "src-rollback") is None
    engine.dispose()
