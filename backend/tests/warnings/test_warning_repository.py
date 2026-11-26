"""Tests for official warning repository persistence, query filters, and validity checks."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic.config import Config
from sqlalchemy.orm import Session

from alembic import command
from app.db.session import create_db_engine, get_session_factory
from app.models.location import LocationModel
from app.models.official_warning import OfficialWarningModel
from app.repositories.warning_repository import OfficialWarningRepository
from app.schemas.common import HazardType
from app.schemas.warning import WarningAuthority, WarningCreate

BACKEND_DIR = Path(__file__).resolve().parents[2]
NOW = datetime.now(UTC)


def _setup_db(tmp_path: Path) -> Session:
    db_url = f"sqlite:///{tmp_path / 'test_warning.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    loc = LocationModel(
        location_id="loc-test-1",
        name="Test Pilot Basin",
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


def test_warning_persistence_and_validity_round_trip(tmp_path: Path) -> None:
    session = _setup_db(tmp_path)
    repo = OfficialWarningRepository(session)

    issued = NOW - timedelta(hours=2)
    valid_until = NOW + timedelta(hours=12)

    warning = WarningCreate(
        warning_id="WARN-PERSIST-01",
        authority=WarningAuthority.CWC,
        hazard_type=HazardType.FLOOD,
        location_id="loc-test-1",
        severity_label="Red",
        headline="Major Flood Alert at Sangam Gauge",
        geographic_scope="Sangam - Anantnag Reach",
        summary="Gauge exceeded alert mark by 0.5m.",
        advisory_notes="Evacuate vulnerable riparian settlements.",
        source_url="https://cwc.gov.in/alerts/sangam",
        source_reference="CWC Northern Basin Daily Bulletin #42",
        issued_at=issued,
        valid_until=valid_until,
        provenance="official:cwc-sangam-42",
        is_demo_fixture=False,
    )

    saved = repo.save(warning)
    assert saved.warning_id == "WARN-PERSIST-01"
    assert saved.is_read_only is True

    fetched = repo.get_by_id("WARN-PERSIST-01")
    assert fetched is not None
    assert fetched.authority == "CWC"
    assert fetched.headline == "Major Flood Alert at Sangam Gauge"
    assert fetched.source_reference == "CWC Northern Basin Daily Bulletin #42"
    assert fetched.is_expired is False

    contract = repo.to_contract(fetched)
    assert contract.is_read_only is True
    assert contract.authority == WarningAuthority.CWC
    assert contract.is_expired is False


def test_expired_warnings_identification(tmp_path: Path) -> None:
    session = _setup_db(tmp_path)
    repo = OfficialWarningRepository(session)

    # Active warning
    active = WarningCreate(
        warning_id="WARN-ACTIVE-01",
        authority=WarningAuthority.DGRE,
        hazard_type=HazardType.AVALANCHE,
        location_id="loc-test-1",
        severity_label="Orange",
        headline="Active Avalanche Watch",
        issued_at=NOW - timedelta(hours=1),
        valid_until=NOW + timedelta(hours=6),
        provenance="official:dgre-active",
    )
    repo.save(active)

    # Expired warning
    expired = WarningCreate(
        warning_id="WARN-EXPIRED-01",
        authority=WarningAuthority.IMD,
        hazard_type=HazardType.FLOOD,
        location_id="loc-test-1",
        severity_label="Yellow",
        headline="Expired Weather Advisory",
        issued_at=NOW - timedelta(days=3),
        valid_until=NOW - timedelta(days=1),
        provenance="official:imd-expired",
    )
    repo.save(expired)

    expired_model = repo.get_by_id("WARN-EXPIRED-01")
    assert expired_model is not None
    assert expired_model.is_expired is True

    # Test filtering by is_expired
    active_items, active_total = repo.list_warnings(is_expired=False)
    assert active_total == 1
    assert active_items[0].warning_id == "WARN-ACTIVE-01"

    expired_items, expired_total = repo.list_warnings(is_expired=True)
    assert expired_total == 1
    assert expired_items[0].warning_id == "WARN-EXPIRED-01"


def test_warning_is_independent_from_model_score(tmp_path: Path) -> None:
    session = _setup_db(tmp_path)
    repo = OfficialWarningRepository(session)

    warning = WarningCreate(
        warning_id="WARN-INDEPENDENT-01",
        authority=WarningAuthority.SDMA,
        hazard_type=HazardType.FLOOD,
        location_id="loc-test-1",
        severity_label="Severe",
        headline="Disaster Authority Flood Order",
        issued_at=NOW - timedelta(hours=2),
        valid_until=NOW + timedelta(hours=10),
        provenance="official:sdma-order-01",
    )
    repo.save(warning)

    fetched = session.get(OfficialWarningModel, "WARN-INDEPENDENT-01")
    assert fetched is not None
    # OfficialWarningModel has no 'score' field; model predictions are strictly kept separate
    assert not hasattr(fetched, "score")
    assert not hasattr(fetched, "risk_class")
    assert fetched.is_read_only is True
