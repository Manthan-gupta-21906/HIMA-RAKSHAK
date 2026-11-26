"""Tests for the observations API endpoints."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.observations import get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.location import LocationModel
from app.models.observation import ObservationModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel
from app.repositories.observation_repository import ObservationRepository
from app.schemas.observation import ObservationContract, ObservationMetric
from app.schemas.source import AccessMode, SourceType, TrustClassification

client = TestClient(app)


@pytest.fixture(autouse=True)
def _setup_test_db(tmp_path: Path) -> Generator[Session, None, None]:
    """Populate test SQLite DB with locations, sources, and observations."""
    db_url = f"sqlite:///{tmp_path / 'test_obs.db'}"
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
        supported_hazards=["flood"],
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

    repo = ObservationRepository(session)
    now = datetime(2026, 11, 26, 12, 0, 0, tzinfo=UTC)
    contracts = [
        ObservationContract(
            observation_id=f"obs-{i}",
            location_id="JK-SGR-01",
            source_id="src-cwc-01",
            observed_at=now - timedelta(hours=i),
            metric=ObservationMetric.RAIN_MM if i % 2 == 0 else ObservationMetric.RIVER_LEVEL_M,
            value=10.0 + i,
            unit="mm" if i % 2 == 0 else "m",
            is_demo_fixture=True,
        )
        for i in range(5)
    ]
    repo.upsert_batch(contracts)
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

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        session.close()


def test_unauthenticated_request_rejected() -> None:
    res = client.get("/observations", params={"location_id": "JK-SGR-01"})
    assert res.status_code == 401
    err = res.json()
    assert err["error_code"] == "HTTP_401"
    assert "timestamp" in err


def test_invalid_query_parameters_return_422_with_envelope() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    # Missing required location_id
    res = client.get("/observations", headers=headers)
    assert res.status_code == 422
    err = res.json()
    assert err["error_code"] == "VALIDATION_ERROR"
    assert len(err["details"]) > 0

    # Invalid page number (ge=1)
    res = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "page": 0},
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["error_code"] == "VALIDATION_ERROR"

    # Invalid page_size (le=100)
    res = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "page_size": 150},
        headers=headers,
    )
    assert res.status_code == 422

    # Invalid metric enum
    res = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "metric": "nonexistent_metric"},
        headers=headers,
    )
    assert res.status_code == 422


def test_list_observations_with_pagination() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "page": 1, "page_size": 2},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2
    assert data["pagination"]["has_next"] is True

    # Page 2
    res2 = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "page": 2, "page_size": 2},
        headers=headers,
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2["items"]) == 2
    assert data2["items"][0]["observation_id"] != data["items"][0]["observation_id"]
    assert data2["pagination"]["has_next"] is True

    # Page 3 (last page with 1 item remaining)
    res3 = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "page": 3, "page_size": 2},
        headers=headers,
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert len(data3["items"]) == 1
    assert data3["pagination"]["has_next"] is False


def test_filter_by_metric() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "metric": "rain_mm"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert all(item["metric"] == "rain_mm" for item in data["items"])
    assert data["total"] == 3


def test_filter_by_date_range() -> None:
    token = create_access_token("viewer1", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    since = "2026-11-26T10:00:00Z"
    until = "2026-11-26T12:00:00Z"
    res = client.get(
        "/observations",
        params={"location_id": "JK-SGR-01", "since": since, "until": until},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
