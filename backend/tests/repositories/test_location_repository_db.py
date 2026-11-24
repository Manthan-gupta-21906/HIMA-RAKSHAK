"""Isolated database integration tests for SqlAlchemyLocationRepository."""

from pathlib import Path

import pytest
from alembic.config import Config

from alembic import command
from app.db.session import create_db_engine, get_session_factory
from app.models.location import LocationRecord
from app.repositories.location_repository import SqlAlchemyLocationRepository
from app.seed.locations import PILOT_LOCATIONS

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture
def isolated_repo(tmp_path: Path) -> SqlAlchemyLocationRepository:
    db_url = f"sqlite:///{tmp_path / 'repo.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session = get_session_factory(engine)()
    try:
        yield SqlAlchemyLocationRepository(session)
    finally:
        session.close()
        engine.dispose()


def test_location_geometry_round_trip(isolated_repo: SqlAlchemyLocationRepository) -> None:
    sample: LocationRecord = PILOT_LOCATIONS[0]
    isolated_repo.upsert(sample)

    loaded = isolated_repo.get_by_id(sample.location_id)
    assert loaded is not None
    assert loaded.location_id == sample.location_id
    assert loaded.geometry_geojson == {
        "type": "Point",
        "coordinates": [sample.longitude, sample.latitude],
    }
    assert loaded.supported_hazards == sample.supported_hazards
    assert isolated_repo.count() == 1
