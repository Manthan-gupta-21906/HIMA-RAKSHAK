"""Tests for transactional persistence, round-trip fidelity, and querying of risk assessments."""

from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from sqlalchemy.orm import Session

from alembic import command
from app.db.session import create_db_engine, get_session_factory
from app.models.location import LocationModel
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.risk import RiskAssessmentContract

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _setup_db(tmp_path: Path) -> Session:
    db_url = f"sqlite:///{tmp_path / 'test_risk.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    # Seed required foreign key location
    loc = LocationModel(
        location_id="loc-test-1",
        name="Test Pilot Basin",
        admin_unit="Kullu, HP",
        latitude=32.24,
        longitude=77.18,
        geom={"type": "Point", "coordinates": [77.18, 32.24]},
        supported_hazards=["flood", "avalanche"],
        coverage_status="supported",
        coverage_note="Fully covered pilot basin",
        is_demo_fixture=True,
        provenance="demo_fixture:test",
    )
    session.add(loc)
    session.commit()
    return session


def _sample_contract(
    risk_id: str = "risk-1",
    location_id: str = "loc-test-1",
    hazard_type: HazardType = HazardType.FLOOD,
    risk_class: RiskClass = RiskClass.HIGH,
    score: float | None = 0.72,
    confidence: float = 0.88,
    lead_time: int = 24,
    freshness: FreshnessStatus = FreshnessStatus.FRESH,
    status: PredictionStatus = PredictionStatus.READY,
    reason: str | None = None,
    assessed_at: datetime | None = None,
) -> RiskAssessmentContract:
    ts = assessed_at or datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    return RiskAssessmentContract(
        risk_id=risk_id,
        location_id=location_id,
        hazard_type=hazard_type,
        risk_class=risk_class,
        score=score,
        confidence=confidence,
        lead_time_hours=lead_time,
        freshness=freshness,
        prediction_status=status,
        readiness_reason=reason,
        assessed_at=ts,
        model_version="test-v1",
        provenance=ProvenanceMeta(
            source_id="src-pilot-1",
            source_name="Pilot Hydro Sensor",
            licence="CC-BY-4.0",
            is_demo_fixture=True,
            ingested_at=ts,
        ),
    )


def test_risk_assessment_persistence_and_round_trip(tmp_path: Path):
    """Verify full fidelity round-trip of uncertainty, freshness, and provenance."""
    session = _setup_db(tmp_path)
    repo = RiskAssessmentRepository(session)

    contract = _sample_contract(
        risk_id="risk-rt-1",
        score=0.68,
        confidence=0.85,
        freshness=FreshnessStatus.FRESH,
        status=PredictionStatus.READY,
    )

    saved = repo.save(contract)
    assert saved.risk_id == "risk-rt-1"

    loaded = repo.get_by_id("risk-rt-1")
    assert loaded is not None
    assert loaded.risk_id == contract.risk_id
    assert loaded.location_id == contract.location_id
    assert loaded.hazard_type == HazardType.FLOOD
    assert loaded.risk_class == RiskClass.HIGH
    assert loaded.score == 0.68
    assert loaded.confidence == 0.85
    assert loaded.freshness == FreshnessStatus.FRESH
    assert loaded.provenance.source_id == "src-pilot-1"
    assert loaded.provenance.is_demo_fixture is True


def test_unsupported_state_persists_without_fake_scores(tmp_path: Path):
    """Verify unsupported state persists with score=None, avoiding fake numerical claims."""
    session = _setup_db(tmp_path)
    repo = RiskAssessmentRepository(session)

    contract = _sample_contract(
        risk_id="risk-unsup-1",
        hazard_type=HazardType.AVALANCHE,
        risk_class=RiskClass.UNSUPPORTED,
        score=None,
        confidence=0.0,
        status=PredictionStatus.UNSUPPORTED,
        reason="Missing snowpack telemetry.",
    )

    repo.save(contract)
    loaded = repo.get_by_id("risk-unsup-1")

    assert loaded is not None
    assert loaded.risk_class == RiskClass.UNSUPPORTED
    assert loaded.score is None
    assert loaded.confidence == 0.0
    assert loaded.prediction_status == PredictionStatus.UNSUPPORTED
    assert loaded.readiness_reason == "Missing snowpack telemetry."


def test_independent_hazard_assessments_persist_co_located(tmp_path: Path):
    """Verify flood and avalanche assessments persist independently for the same location."""
    session = _setup_db(tmp_path)
    repo = RiskAssessmentRepository(session)
    t0 = datetime(2026, 11, 26, 10, 0, tzinfo=UTC)

    flood = _sample_contract(
        risk_id="risk-flood-loc1",
        hazard_type=HazardType.FLOOD,
        risk_class=RiskClass.MODERATE,
        score=0.45,
        assessed_at=t0,
    )
    avalanche = _sample_contract(
        risk_id="risk-avalanche-loc1",
        hazard_type=HazardType.AVALANCHE,
        risk_class=RiskClass.HIGH,
        score=0.75,
        assessed_at=t0,
    )

    repo.save(flood)
    repo.save(avalanche)

    latest_flood = repo.get_latest_for_location_and_hazard(
        "loc-test-1", HazardType.FLOOD
    )
    latest_avalanche = repo.get_latest_for_location_and_hazard(
        "loc-test-1", HazardType.AVALANCHE
    )

    assert latest_flood is not None
    assert latest_flood.hazard_type == HazardType.FLOOD
    assert latest_flood.score == 0.45

    assert latest_avalanche is not None
    assert latest_avalanche.hazard_type == HazardType.AVALANCHE
    assert latest_avalanche.score == 0.75

    history = repo.list_history("loc-test-1")
    assert len(history) == 2
