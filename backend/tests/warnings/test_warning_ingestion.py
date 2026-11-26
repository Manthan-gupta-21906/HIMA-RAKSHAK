"""Tests for official warning ingestion and sample fixture preservation."""

from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from sqlalchemy.orm import Session

from alembic import command
from app.db.session import create_db_engine, get_session_factory
from app.ingestion.warning_import import (
    SAMPLE_WARNING_FIXTURES,
    import_sample_fixtures,
    import_warning_record,
    load_sample_warning_fixtures,
)
from app.models.location import LocationModel
from app.models.official_warning import OfficialWarningModel
from app.schemas.warning import WarningAuthority

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _setup_db(tmp_path: Path) -> Session:
    db_url = f"sqlite:///{tmp_path / 'test_ingest.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    loc = LocationModel(
        location_id="loc-test-1",
        name="Test Basin",
        admin_unit="Kullu, HP",
        latitude=31.9566,
        longitude=77.1095,
        geom={"type": "Point", "coordinates": [77.1095, 31.9566]},
        supported_hazards=["flood", "avalanche"],
        coverage_status="supported",
        coverage_note="Pilot catchment",
        is_demo_fixture=True,
        provenance="official:test-location",
    )
    session.add(loc)
    session.commit()
    return session


def test_sample_warning_fixtures_are_clearly_labelled() -> None:
    fixtures = load_sample_warning_fixtures()
    assert len(fixtures) >= 3

    for item in fixtures:
        # Verify clear labelling as sample/demo fixture
        assert item.is_demo_fixture is True
        assert item.authority in (WarningAuthority.CWC, WarningAuthority.DGRE, WarningAuthority.IMD, WarningAuthority.SDMA)
        assert item.source_reference is not None
        assert "Sample" in item.source_reference
        # Verify valid window logic
        assert item.valid_until > item.issued_at


def test_import_warning_fixtures_into_db(tmp_path: Path) -> None:
    session = _setup_db(tmp_path)
    imported = import_sample_fixtures(session)

    assert len(imported) == len(SAMPLE_WARNING_FIXTURES)
    for model in imported:
        assert isinstance(model, OfficialWarningModel)
        assert model.is_read_only is True
        assert model.is_demo_fixture is True

    # Ensure idempotency / upsert preserves authority content
    cwc_warning = session.get(OfficialWarningModel, "WARN-CWC-2026-104")
    assert cwc_warning is not None
    assert cwc_warning.authority == "CWC"
    assert "Flash Flood Watch" in cwc_warning.headline
    assert cwc_warning.source_url == "https://cwc.gov.in/bulletins/north/2026-104"
