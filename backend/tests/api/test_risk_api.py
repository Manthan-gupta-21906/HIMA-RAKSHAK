"""Tests for the risk assessment API endpoints."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.risk import _get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.location import LocationModel
from app.models.observation import ObservationModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.risk import RiskAssessmentContract
from app.schemas.source import AccessMode, SourceType, TrustClassification

client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup_test_db(tmp_path: Path) -> Generator[Session, None, None]:
    """Populate test SQLite DB with locations and risk assessments."""
    db_url = f"sqlite:///{tmp_path / 'test_risk.db'}"
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
        source_type=SourceType.HYDROLOGY.value,
        trust_classification=TrustClassification.AUTHORITATIVE.value,
        access_mode=AccessMode.LIVE.value,
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

    # 3 flood assessments (different timestamps)
    for i in range(3):
        repo.save(
            RiskAssessmentContract(
                risk_id=f"risk-flood-{i}",
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

    # 1 avalanche assessment
    repo.save(
        RiskAssessmentContract(
            risk_id="risk-aval-0",
            location_id="JK-SGR-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.LOW,
            score=0.20,
            confidence=0.75,
            lead_time_hours=48,
            freshness=FreshnessStatus.FRESH,
            prediction_status=PredictionStatus.READY,
            readiness_reason=None,
            assessed_at=now,
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

    app.dependency_overrides[_get_db] = _override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(_get_db, None)
        session.close()


def test_unauthenticated_risk_requests_rejected() -> None:
    res = client.get("/risk/current/JK-SGR-01")
    assert res.status_code == 401
    assert res.json()["error_code"] == "HTTP_401"

    res_hist = client.get("/risk/history/JK-SGR-01")
    assert res_hist.status_code == 401

    res_state = client.get("/risk/state/JK-SGR-01")
    assert res_state.status_code == 401


def test_get_current_risk_returns_latest_per_hazard() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/risk/current/JK-SGR-01", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "flood" in data
    assert "avalanche" in data
    assert data["flood"]["risk_id"] == "risk-flood-0"
    assert data["flood"]["score"] == 0.85
    assert data["avalanche"]["risk_id"] == "risk-aval-0"


def test_get_risk_history_with_pagination_and_filters() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    # History filtered by flood hazard
    res = client.get(
        "/risk/history/JK-SGR-01",
        params={"hazard_type": "flood", "page": 1, "page_size": 2},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2
    assert data["pagination"]["has_next"] is True
    assert all(item["hazard_type"] == "flood" for item in data["items"])

    # Page 2
    res2 = client.get(
        "/risk/history/JK-SGR-01",
        params={"hazard_type": "flood", "page": 2, "page_size": 2},
        headers=headers,
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 1
    assert data2["pagination"]["has_next"] is False


def test_get_risk_state_unified() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/risk/state/JK-SGR-01", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["location_id"] == "JK-SGR-01"
    assert data["flood"] is not None
    assert data["avalanche"] is not None
    assert data["primary_hazard"] == "flood"
    assert data["highest_risk_class"] == "high"


def test_get_risk_state_unknown_location_returns_404() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/risk/state/JK-UNKNOWN-99", headers=headers)
    assert res.status_code == 404
    err = res.json()
    assert err["error_code"] == "HTTP_404"
    assert "No risk assessments found" in err["message"]


def test_invalid_risk_query_params_return_422() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid hazard_type enum
    res = client.get(
        "/risk/history/JK-SGR-01",
        params={"hazard_type": "earthquake"},
        headers=headers,
    )
    assert res.status_code == 422
    err = res.json()
    assert err["error_code"] == "VALIDATION_ERROR"


def test_assess_location_risk_requires_operator_auth() -> None:
    # Unauthenticated -> 401
    res_unauth = client.post("/risk/assess/JK-SGR-01")
    assert res_unauth.status_code == 401
    assert res_unauth.json()["error_code"] == "HTTP_401"

    # Viewer -> 403
    viewer_token = create_access_token("viewer1", "viewer")
    res_viewer = client.post(
        "/risk/assess/JK-SGR-01",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert res_viewer.status_code == 403
    assert res_viewer.json()["error_code"] == "HTTP_403"


def test_assess_location_risk_missing_location_returns_404() -> None:
    op_token = create_access_token("op1", "district_operator")
    res = client.post(
        "/risk/assess/JK-MISSING-99",
        headers={"Authorization": f"Bearer {op_token}"},
    )
    assert res.status_code == 404
    err = res.json()
    assert err["error_code"] == "HTTP_404"
    assert "JK-MISSING-99" in err["message"]


def test_assess_location_risk_persists_and_updates_retrieval_endpoints() -> None:
    op_token = create_access_token("op1", "district_operator")
    headers = {"Authorization": f"Bearer {op_token}"}
    cutoff_iso = "2026-11-26T18:00:00Z"

    res = client.post(
        "/risk/assess/JK-SGR-01",
        json={"cutoff_at": cutoff_iso},
        headers=headers,
    )
    assert res.status_code == 200
    state = res.json()
    assert state["location_id"] == "JK-SGR-01"
    assert state["flood"] is not None
    assert state["flood"]["prediction_status"] == "unsupported"
    assert state["flood"]["score"] is None
    assert state["avalanche"] is not None
    assert state["avalanche"]["prediction_status"] == "unsupported"
    assert state["avalanche"]["score"] is None

    # Verify newly persisted assessments are returned by /risk/current and /risk/state
    current_res = client.get("/risk/current/JK-SGR-01", headers=headers)
    assert current_res.status_code == 200
    current = current_res.json()
    assert current["flood"]["risk_id"] == state["flood"]["risk_id"]
    assert current["avalanche"]["risk_id"] == state["avalanche"]["risk_id"]

    state_res = client.get("/risk/state/JK-SGR-01", headers=headers)
    assert state_res.status_code == 200
    assert state_res.json()["flood"]["risk_id"] == state["flood"]["risk_id"]

    history_res = client.get("/risk/history/JK-SGR-01", headers=headers)
    assert history_res.status_code == 200
    history_ids = {item["risk_id"] for item in history_res.json()["items"]}
    assert state["flood"]["risk_id"] in history_ids
    assert state["avalanche"]["risk_id"] in history_ids
