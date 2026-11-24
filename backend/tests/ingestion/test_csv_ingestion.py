"""Tests for CSV observation ingestion, column mapping, idempotency, and DB transactions."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy.orm import Session

from alembic import command
from app.db.session import create_db_engine, get_db, get_session_factory
from app.ingestion.column_mapping import ColumnMapping
from app.models.location import LocationModel
from app.models.source import SourceModel
from app.repositories.observation_repository import ObservationRepository
from app.repositories.source_repository import SourceNotFoundError, SourceRepository
from app.services.ingestion_service import IngestionService

BACKEND_DIR = Path(__file__).resolve().parents[2]
FIXTURE_CSV = BACKEND_DIR.parent / "data" / "fixtures" / "sample_observations.csv"


def _create_migrated_session(tmp_path: Path) -> tuple[Session, object]:
    """Create an isolated SQLite DB migrated to head and seeded with pilot location + source."""
    db_url = f"sqlite:///{tmp_path / 'obs_test.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    factory = get_session_factory(engine)
    db = factory()

    for loc_id, name in [
        ("JK-SGR-01", "Srinagar"),
        ("UK-JSH-01", "Joshimath"),
        ("LA-DRS-01", "Drass"),
    ]:
        db.add(
            LocationModel(
                location_id=loc_id,
                name=name,
                admin_unit="Demo District",
                latitude=34.0,
                longitude=75.0,
                geom={"type": "Point", "coordinates": [75.0, 34.0]},
                supported_hazards=["flood"],
                coverage_status="supported",
                coverage_note="Demo fixture",
                is_demo_fixture=True,
                provenance="test-fixture",
            )
        )

    db.add(
        SourceModel(
            source_id="imd-demo-csv",
            source_name="IMD Demo CSV",
            provider="IMD",
            dataset="Demo CSV",
            source_type="weather",
            access_mode="sample",
            licence="CC-BY-4.0",
            reference_url="",
            update_frequency_minutes=60,
            trust_classification="demo",
            is_authoritative=False,
            is_demo_fixture=True,
        )
    )
    db.commit()
    return db, factory


def test_ingest_demo_fixture_and_idempotency(tmp_path: Path) -> None:
    db, _ = _create_migrated_session(tmp_path)
    try:
        svc = IngestionService(ObservationRepository(db), SourceRepository(db))
        summary = svc.ingest_csv(FIXTURE_CSV, source_id="imd-demo-csv")
        db.commit()

        assert summary.total_rows == 6
        assert summary.valid_rows == 6
        assert summary.inserted == 6
        assert summary.skipped_duplicates == 0
        assert summary.error_count == 0

        # Verify source and observed timestamps persisted
        rows = ObservationRepository(db).list_by_location("JK-SGR-01")
        assert len(rows) == 2
        assert all(r.source_id == "imd-demo-csv" for r in rows)
        assert rows[0].observed_at.replace(tzinfo=UTC) == datetime(
            2026, 11, 25, 0, 0, tzinfo=UTC
        )

        # Repeated import must be idempotent
        repeat = svc.ingest_csv(FIXTURE_CSV, source_id="imd-demo-csv")
        db.commit()
        assert repeat.inserted == 0
        assert repeat.skipped_duplicates == 6
        assert ObservationRepository(db).count() == 6
    finally:
        db.close()


def test_custom_column_mapping_and_unit_normalization(tmp_path: Path) -> None:
    db, _ = _create_migrated_session(tmp_path)
    try:
        csv_text = (
            "station,ts,var,val,uom\n"
            "LA-DRS-01,2026-11-25T01:00:00+05:30,wind_kmh,10.0,m/s\n"
            "LA-DRS-01,2026-11-25T01:00:00+05:30,temp_c,-4.2,degC\n"
        )
        mapping = ColumnMapping(
            location_id="station",
            observed_at="ts",
            metric="var",
            value="val",
            unit="uom",
            observation_id=None,
        )
        svc = IngestionService(ObservationRepository(db), SourceRepository(db))
        summary = svc.ingest_csv(csv_text, source_id="imd-demo-csv", mapping=mapping)
        db.commit()

        assert summary.inserted == 2
        assert summary.error_count == 0
        obs = ObservationRepository(db).list_by_location("LA-DRS-01", metric="wind_kmh")
        assert obs[0].value == pytest.approx(36.0)
        assert obs[0].unit == "km/h"
    finally:
        db.close()


def test_invalid_rows_reported_while_valid_rows_persist(tmp_path: Path) -> None:
    db, _ = _create_migrated_session(tmp_path)
    try:
        csv_text = (
            "location_id,observed_at,metric,value,unit\n"
            "JK-SGR-01,2026-11-25T02:00:00Z,rain_mm,12.0,mm\n"
            "JK-SGR-01,2026-11-25T02:00:00,rain_mm,5.0,mm\n"  # naive timestamp
            "JK-SGR-01,2026-11-25T02:00:00Z,rain_mm,9.0,liters\n"  # invalid unit
            "JK-SGR-01,2026-11-25T02:00:00Z,unknown_metric,1.0,mm\n"  # bad metric
        )
        svc = IngestionService(ObservationRepository(db), SourceRepository(db))
        summary = svc.ingest_csv(csv_text, source_id="imd-demo-csv")
        db.commit()

        assert summary.total_rows == 4
        assert summary.valid_rows == 1
        assert summary.inserted == 1
        assert summary.error_count == 3
        assert [e.row_number for e in summary.errors] == [3, 4, 5]
    finally:
        db.close()


def test_unknown_source_rejected(tmp_path: Path) -> None:
    db, _ = _create_migrated_session(tmp_path)
    try:
        svc = IngestionService(ObservationRepository(db), SourceRepository(db))
        with pytest.raises(SourceNotFoundError):
            svc.ingest_csv(FIXTURE_CSV, source_id="nonexistent-source")
    finally:
        db.close()


def test_db_transaction_rollback_on_error(tmp_path: Path) -> None:
    db, factory = _create_migrated_session(tmp_path)
    db.close()

    gen = get_db(factory)  # type: ignore[arg-type]
    session = next(gen)
    svc = IngestionService(ObservationRepository(session), SourceRepository(session))
    svc.ingest_csv(FIXTURE_CSV, source_id="imd-demo-csv")

    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError("Simulated failure after flush"))

    # Verify rollback left observations table empty
    verify_db = factory()  # type: ignore[operator]
    try:
        assert ObservationRepository(verify_db).count() == 0
    finally:
        verify_db.close()
