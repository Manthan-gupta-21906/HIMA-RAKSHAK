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

    loc2 = LocationModel(
        location_id="JK-GUL-01",
        name="Gulmarg — Affarwat Ridge",
        admin_unit="Baramulla District, J&K",
        latitude=34.0484,
        longitude=74.3805,
        geom={"type": "Point", "coordinates": [74.3805, 34.0484]},
        supported_hazards=["flood", "avalanche"],
        coverage_status="partial",
        coverage_note="Avalanche-prone ridge",
        is_demo_fixture=True,
        provenance="demo_fixture:test",
    )
    session.add(loc2)

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

    # 2 flood assessments for JK-GUL-01
    for i in range(2):
        repo.save(
            RiskAssessmentContract(
                risk_id=f"risk-flood-gul-{i}",
                location_id="JK-GUL-01",
                hazard_type=HazardType.FLOOD,
                risk_class=RiskClass.MODERATE if i == 0 else RiskClass.HIGH,
                score=0.55 if i == 0 else 0.85,
                confidence=0.80,
                lead_time_hours=24,
                freshness=FreshnessStatus.FRESH,
                prediction_status=PredictionStatus.READY,
                readiness_reason=None,
                assessed_at=now - timedelta(hours=i * 8),
                model_version="flood-baseline-v1",
                provenance=provenance,
            )
        )

    # 1 avalanche assessment for JK-GUL-01
    repo.save(
        RiskAssessmentContract(
            risk_id="risk-aval-gul-0",
            location_id="JK-GUL-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.HIGH,
            score=0.90,
            confidence=0.85,
            lead_time_hours=48,
            freshness=FreshnessStatus.FRESH,
            prediction_status=PredictionStatus.READY,
            readiness_reason=None,
            assessed_at=now - timedelta(hours=24),
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


def test_replay_without_location_id() -> None:
    """Replay without a location filter returns events across all locations."""
    res = client.get("/risk/replay", headers=_headers("viewer"))
    assert res.status_code == 200

    data = res.json()
    # JK-SGR-01: flood + avalanche = 2 events
    # JK-GUL-01: flood + avalanche = 2 events
    assert data["total"] == 4
    assert len(data["items"]) == 4


def test_replay_with_invalid_location_id_returns_404() -> None:
    """Replay with an unknown location ID returns 404."""
    res = client.get("/risk/replay?location_id=JK-NONEXISTENT", headers=_headers("viewer"))
    assert res.status_code == 404
    assert "JK-NONEXISTENT" in res.json()["message"]


def test_replay_empty_results() -> None:
    """Replay with filters matching no assessments returns empty items."""
    res = client.get(
        "/risk/replay?location_id=JK-SGR-01&since=2027-01-01T00:00:00Z",
        headers=_headers("viewer"),
    )
    assert res.status_code == 200

    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_replay_date_filter() -> None:
    """Replay with a since filter returns only assessments on or after that time."""
    since_iso = "2026-11-26T18:00:00Z"
    res = client.get(
        f"/risk/replay?location_id=JK-SGR-01&since={since_iso}",
        headers=_headers("viewer"),
    )
    assert res.status_code == 200

    data = res.json()
    # Assessments at 12:00, 06:00, 00:00, and previous day 18:00 (4 flood)
    # Assessments at 12:00 and 00:00 (2 avalanche)
    # With since=18:00 on Nov 26, assessments before that are excluded
    for item in data["items"]:
        for frame in item["frames"]:
            assert frame["timestamp"] >= since_iso


def test_replay_hazard_and_location_filters_combined() -> None:
    """Replay with both location_id and hazard_type filters works together."""
    res = client.get(
        "/risk/replay?location_id=JK-SGR-01&hazard_type=flood",
        headers=_headers("viewer"),
    )
    assert res.status_code == 200

    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["hazard"] == "flood"
    assert len(data["items"][0]["frames"]) == 4


def test_replay_without_location_groups_by_location() -> None:
    """Replay without a location filter returns one event per location+hazard."""
    res = client.get("/risk/replay", headers=_headers("viewer"))
    assert res.status_code == 200

    data = res.json()
    # JK-SGR-01: flood + avalanche = 2 events
    # JK-GUL-01: flood + avalanche = 2 events
    assert data["total"] == 4
    assert len(data["items"]) == 4

    # Each event should contain frames from only one location
    for event in data["items"]:
        event_loc = event["location_id"]
        event_hazard = event["hazard"]
        for frame in event["frames"]:
            # The frame's timestamp belongs to an assessment for this location+hazard
            pass  # Frames don't carry location_id, but we verify via event-level fields

        if event_loc == "JK-SGR-01":
            assert event["sector"] == "Srinagar District, J&K"
            assert event["is_demo_fixture"] is True
        elif event_loc == "JK-GUL-01":
            assert event["sector"] == "Baramulla District, J&K"
            assert event["is_demo_fixture"] is True


def test_replay_no_event_mixes_locations() -> None:
    """Assert that no replay event contains frames from another location."""
    res = client.get("/risk/replay", headers=_headers("viewer"))
    assert res.status_code == 200

    data = res.json()

    # Build expected frame counts per location+hazard
    expected = {
        ("JK-SGR-01", "flood"): 4,
        ("JK-SGR-01", "avalanche"): 2,
        ("JK-GUL-01", "flood"): 2,
        ("JK-GUL-01", "avalanche"): 1,
    }

    found: dict[tuple[str, str], int] = {}
    for event in data["items"]:
        key = (event["location_id"], event["hazard"])
        found[key] = len(event["frames"])
        # No frame from another location should appear here
        assert key in expected, f"Unexpected event: {key}"

    assert found == expected


def test_replay_per_location_sector_and_provenance() -> None:
    """Each replay event returns its location's sector and demo-fixture flag."""
    res = client.get("/risk/replay", headers=_headers("viewer"))
    assert res.status_code == 200

    data = res.json()

    sgr_events = [e for e in data["items"] if e["location_id"] == "JK-SGR-01"]
    gul_events = [e for e in data["items"] if e["location_id"] == "JK-GUL-01"]

    assert len(sgr_events) == 2
    assert len(gul_events) == 2

    for event in sgr_events:
        assert event["sector"] == "Srinagar District, J&K"
        assert event["is_demo_fixture"] is True

    for event in gul_events:
        assert event["sector"] == "Baramulla District, J&K"
        assert event["is_demo_fixture"] is True
