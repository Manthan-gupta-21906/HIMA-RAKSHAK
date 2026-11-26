"""Tests for POST /observations — authenticated field observation submission."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.observations import _get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.location import LocationModel
from app.models.observation import ObservationModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel
from app.schemas.source import AccessMode, SourceType, TrustClassification

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _setup_post_test_db(tmp_path: Path) -> Generator[Session, None, None]:
    """Set up an isolated SQLite DB with one flood-capable and one avalanche-capable location."""
    db_url = f"sqlite:///{tmp_path / 'test_obs_post.db'}"
    engine = create_db_engine(db_url)
    Base.metadata.create_all(bind=engine)
    session_factory = get_session_factory(engine)
    session = session_factory()

    # Location that supports flood only
    flood_loc = LocationModel(
        location_id="JK-SGR-01",
        name="Srinagar — Dal Lake Basin",
        admin_unit="Srinagar District, J&K",
        latitude=34.0837,
        longitude=74.7973,
        geom={"type": "Point", "coordinates": [74.7973, 34.0837]},
        supported_hazards=["flood"],
        coverage_status="supported",
        coverage_note="Pilot basin",
        is_demo_fixture=True,
        provenance="demo_fixture:test",
    )
    # Location that supports avalanche only
    avy_loc = LocationModel(
        location_id="JK-PN-04",
        name="Poonch — Surankote Pass",
        admin_unit="Poonch District, J&K",
        latitude=33.6500,
        longitude=74.1300,
        geom={"type": "Point", "coordinates": [74.1300, 33.6500]},
        supported_hazards=["avalanche"],
        coverage_status="supported",
        coverage_note="Avalanche pilot site",
        is_demo_fixture=True,
        provenance="demo_fixture:test",
    )
    # Pre-existing source (not the default field-obs source)
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
    session.add_all([flood_loc, avy_loc, src])
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _operator_headers() -> dict[str, str]:
    token = create_access_token("op1", "district_operator")
    return {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    token = create_access_token("admin1", "admin")
    return {"Authorization": f"Bearer {token}"}


def _viewer_headers() -> dict[str, str]:
    token = create_access_token("viewer1", "viewer")
    return {"Authorization": f"Bearer {token}"}


def _valid_flood_payload(**overrides: object) -> dict:
    base: dict = {
        "location_id": "JK-SGR-01",
        "hazard_type": "flood",
        "metric": "rain_mm",
        "value": 42.5,
        "unit": "mm",
        "notes": "Heavy rainfall observed at the gauge station.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------

def test_create_observation_valid_operator() -> None:
    """District operator submits valid flood observation → 201 with full contract."""
    res = client.post("/observations", json=_valid_flood_payload(), headers=_operator_headers())
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["location_id"] == "JK-SGR-01"
    assert data["metric"] == "rain_mm"
    assert data["value"] == 42.5
    assert data["unit"] == "mm"
    assert data["is_demo_fixture"] is False
    assert "observation_id" in data
    assert "observed_at" in data


def test_create_observation_valid_admin() -> None:
    """Admin submits a valid avalanche observation → 201."""
    payload = {
        "location_id": "JK-PN-04",
        "hazard_type": "avalanche",
        "metric": "snow_depth_cm",
        "value": 120.0,
        "unit": "cm",
    }
    res = client.post("/observations", json=payload, headers=_admin_headers())
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["metric"] == "snow_depth_cm"
    assert data["value"] == 120.0


def test_create_observation_metric_inferred_from_hazard_type() -> None:
    """When metric is omitted, it is inferred from hazard_type."""
    payload = {
        "location_id": "JK-SGR-01",
        "hazard_type": "flood",   # metric omitted → inferred as river_level_m
        "value": 3.2,
        "unit": "m",
    }
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["metric"] == "river_level_m"


def test_create_observation_unit_normalised() -> None:
    """Non-canonical unit is normalised transparently (ft → m for river_level_m)."""
    payload = {
        "location_id": "JK-SGR-01",
        "hazard_type": "flood",
        "metric": "river_level_m",
        "value": 10.0,  # 10 ft → ~3.048 m
        "unit": "ft",
    }
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["unit"] == "m"
    assert abs(data["value"] - 3.048) < 0.01


def test_create_observation_idempotent() -> None:
    """Submitting the same observation twice returns the first result without duplication."""
    now = datetime.now(UTC).isoformat()
    payload = {**_valid_flood_payload(), "observed_at": now}
    res1 = client.post("/observations", json=payload, headers=_operator_headers())
    assert res1.status_code == 201, res1.text
    obs_id_1 = res1.json()["observation_id"]

    res2 = client.post("/observations", json=payload, headers=_operator_headers())
    assert res2.status_code == 201, res2.text
    # Must return the same record, not a new insert
    assert res2.json()["observation_id"] == obs_id_1


def test_create_observation_auto_creates_field_obs_source() -> None:
    """Auto-creates the default 'src-field-obs' source when it does not exist."""
    payload = _valid_flood_payload()
    # source_id defaults to "src-field-obs" which is not in the DB fixture
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 201, res.text
    assert res.json()["source_id"] == "src-field-obs"


# ---------------------------------------------------------------------------
# Auth / role failures
# ---------------------------------------------------------------------------

def test_create_observation_unauthenticated_rejected() -> None:
    """No auth token → 401."""
    res = client.post("/observations", json=_valid_flood_payload())
    assert res.status_code == 401


def test_create_observation_viewer_forbidden() -> None:
    """Viewer role cannot submit observations → 403."""
    res = client.post("/observations", json=_valid_flood_payload(), headers=_viewer_headers())
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Location / hazard failures
# ---------------------------------------------------------------------------

def test_create_observation_unknown_location() -> None:
    """Non-existent location_id → 404."""
    payload = _valid_flood_payload(location_id="NONEXISTENT-99")
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 404
    assert "NONEXISTENT-99" in res.json()["detail"]


def test_create_observation_incompatible_hazard() -> None:
    """Flood metric submitted to an avalanche-only location → 422."""
    payload = {
        "location_id": "JK-PN-04",   # supports only avalanche
        "hazard_type": "flood",
        "metric": "rain_mm",
        "value": 10.0,
        "unit": "mm",
    }
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------

def test_create_observation_negative_value_rejected() -> None:
    """Negative rain value → 422."""
    payload = _valid_flood_payload(value=-5.0)
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


def test_create_observation_out_of_bounds_rejected() -> None:
    """Rain value above physical ceiling (>2000 mm) → 422."""
    payload = _valid_flood_payload(value=9999.9)
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


def test_create_observation_future_timestamp_rejected() -> None:
    """Timestamp more than 5 minutes in the future → 422."""
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    payload = _valid_flood_payload(observed_at=future)
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


def test_create_observation_ancient_timestamp_rejected() -> None:
    """Timestamp older than 365 days → 422."""
    old = (datetime.now(UTC) - timedelta(days=400)).isoformat()
    payload = _valid_flood_payload(observed_at=old)
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


def test_create_observation_bad_unit_rejected() -> None:
    """Unrecognised unit that cannot be normalised → 422."""
    payload = _valid_flood_payload(metric="rain_mm", unit="furlongs")
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


def test_create_observation_incompatible_metric_hazard_pair() -> None:
    """Metric incompatible with the stated hazard_type → 422."""
    payload = {
        "location_id": "JK-SGR-01",
        "hazard_type": "flood",
        "metric": "snow_depth_cm",   # snow is an avalanche metric
        "value": 50.0,
        "unit": "cm",
    }
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422


def test_create_observation_missing_required_fields() -> None:
    """Payload missing required fields (value, unit) → 422."""
    res = client.post(
        "/observations",
        json={"location_id": "JK-SGR-01"},
        headers=_operator_headers(),
    )
    assert res.status_code == 422


def test_create_observation_no_metric_no_hazard_rejected() -> None:
    """Neither metric nor hazard_type → 422 (cannot infer metric)."""
    payload = {
        "location_id": "JK-SGR-01",
        "value": 5.0,
        "unit": "mm",
    }
    res = client.post("/observations", json=payload, headers=_operator_headers())
    assert res.status_code == 422
