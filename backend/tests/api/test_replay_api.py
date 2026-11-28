"""API tests for the historical replay endpoint."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import risk as risk_routes
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.location import LocationModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel  # noqa: F401
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.risk import RiskAssessmentContract

client = TestClient(app)


@pytest.fixture(autouse=True)
def _replay_test_db(tmp_path: Path) -> Generator[Session, None, None]:
    """Populate test SQLite DB with a location and risk assessment history."""
    db_url = f"sqlite:///{tmp_path / 'test_replay.db'}"
    engine = create_db_engine(db_url)
    Base.metadata.create_all(bind=engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    loc = LocationModel(
        location_id="JK-SGR-01",
        name="Srinagar — Dal Lake Basin",
        admin_unit="Srinagar District, J&K",
        latitude=34.0837,
        longitude=74.7973,
        geom={"type": "Point", "coordinates": [74.7973, 34.0837]},
        supported_hazards=["flood", "avalanche"],
        coverage_status="supported",
        coverage_note="Fully covered pilot basin",
        is_demo_fixture=True,
        provenance="demo_fixture:test",
    )
    session.add(loc)

    src = SourceModel(
        source_id="src-cwc-01",
        source_name="Central Water Commission",
        provider="CWC",
        dataset="telemetry",
        source_type="hydrology",
        trust_classification="authoritative",
        access_mode="live",
        update_frequency_minutes=60,
        licence="Government Open Data Licence - India (GODL)",
    )
    session.add(src)
    session.commit()

    repo = RiskAssessmentRepository(session)
    now = datetime(2026, 11, 26, 12, 0, 0, tzinfo=UTC)

    provenance = ProvenanceMeta(
        source_id="src-cwc-01",
        source_name="Central Water Commission",
        licence="GODL",
        is_demo_fixture=True,
        ingested_at=now,
    )

    # 4 flood assessments at different timestamps (chronological order when reversed)
    for i in range(4):
        repo.save(
            RiskAssessmentContract(
                risk_id=f"risk-flood-replay-{i}",
                location_id="JK-SGR-01",
                hazard_type=HazardType.FLOOD,
                risk_class=RiskClass.HIGH if i == 0 else RiskClass.MODERATE,
                score=0.85 if i == 0 else 0.55,
                confidence=0.88,
                lead_time_hours=24,
                freshness=FreshnessStatus.FRESH,
                prediction_status=PredictionStatus.READY,
                readiness_reason=None,
                assessed_at=now - timedelta(hours=i * 6),
                model_version="flood-baseline-v1",
                provenance=provenance,
            )
        )

    # 2 avalanche assessments
    for i in range(2):
        repo.save(
            RiskAssessmentContract(
                risk_id=f"risk-aval-replay-{i}",
                location_id="JK-SGR-01",
                hazard_type=HazardType.AVALANCHE,
                risk_class=RiskClass.LOW if i == 0 else RiskClass.MODERATE,
                score=0.20 if i == 0 else 0.45,
                confidence=0.75,
                lead_time_hours=48,
                freshness=FreshnessStatus.FRESH,
                prediction_status=PredictionStatus.READY,
                readiness_reason=None,
                assessed_at=now - timedelta(hours=i * 12),
                model_version="aval-gated-v1",
                provenance=provenance,
            )
        )
    session.commit()

    def _override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app.dependency_overrides[risk_routes._get_db] = _override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(risk_routes._get_db, None)
        session.close()


def _headers(role: str) -> dict[str, str]:
    token = create_access_token(f"{role}_user", role)
    return {"Authorization": f"Bearer {token}"}


def test_replay_requires_authentication() -> None:
    assert client.get("/risk/replay?location_id=JK-SGR-01").status_code == 401


def test_viewer_can_list_replay_events() -> None:
    res = client.get("/risk/replay?location_id=JK-SGR-01", headers=_headers("viewer"))
    assert res.status_code == 200

    data = res.json()
    assert data["total"] == 2  # one flood event + one avalanche event
    assert len(data["items"]) == 2

    flood_event = next(e for e in data["items"] if e["hazard"] == "flood")
    assert flood_event["location_id"] == "JK-SGR-01"
    assert flood_event["sector"] == "Srinagar District, J&K"
    assert len(flood_event["frames"]) == 4
    assert flood_event["is_demo_fixture"] is True

    # Frames are chronological (oldest first)
    frames = flood_event["frames"]
    assert frames[0]["timestamp"] < frames[-1]["timestamp"]
    assert frames[0]["alert_tier"] == "Watch"  # MODERATE
    assert frames[-1]["alert_tier"] == "High Risk"  # HIGH
    assert frames[0]["risk_class"] == "moderate"
    assert frames[-1]["risk_class"] == "high"


def test_replay_hazard_type_filter() -> None:
    res = client.get(
        "/risk/replay?location_id=JK-SGR-01&hazard_type=avalanche",
        headers=_headers("viewer"),
    )
    assert res.status_code == 200

    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["hazard"] == "avalanche"
    assert len(data["items"][0]["frames"]) == 2


def test_replay_unknown_location_returns_404() -> None:
    res = client.get("/risk/replay?location_id=JK-UNKNOWN-99", headers=_headers("viewer"))
    assert res.status_code == 404
    assert "JK-UNKNOWN-99" in res.json()["message"]


def test_replay_frame_structure() -> None:
    res = client.get("/risk/replay?location_id=JK-SGR-01", headers=_headers("viewer"))
    assert res.status_code == 200

    frame = res.json()["items"][0]["frames"][0]
    required_fields = {
        "id",
        "timestamp",
        "phase_label",
        "primary_metric_label",
        "primary_metric_value",
        "secondary_metric_label",
        "secondary_metric_value",
        "alert_tier",
        "risk_class",
        "score",
        "confidence",
        "summary",
    }
    assert required_fields.issubset(set(frame.keys()))
