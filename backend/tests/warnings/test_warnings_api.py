"""Tests for official warnings API endpoints, role permissions, and filtering."""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.warnings import _get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.location import LocationModel
from app.models.official_warning import OfficialWarningModel
from app.schemas.common import HazardType
from app.schemas.warning import WarningAuthority

client = TestClient(app)
NOW = datetime.now(UTC)


@pytest.fixture(autouse=True)
def _setup_test_db(tmp_path: Path) -> Generator[Session, None, None]:
    db_url = f"sqlite:///{tmp_path / 'test_warnings_api.db'}"
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
        provenance="official:test-location",
    )
    session.add(loc)

    # Active warning
    session.add(
        OfficialWarningModel(
            warning_id="WARN-ACTIVE-1",
            authority=WarningAuthority.CWC.value,
            hazard_type=HazardType.FLOOD.value,
            location_id="JK-SGR-01",
            severity_label="Red",
            headline="Severe Flood Warning",
            geographic_scope="Srinagar Basin",
            summary="Gauge above threshold.",
            advisory_notes="Stand by for evacuation.",
            source_url="https://cwc.gov.in/warn/1",
            source_reference="CWC Bulletin #1",
            issued_at=NOW - timedelta(hours=2),
            valid_until=NOW + timedelta(hours=10),
            is_read_only=True,
            provenance="official:cwc-1",
            is_demo_fixture=True,
            ingested_at=NOW,
        )
    )

    # Expired warning
    session.add(
        OfficialWarningModel(
            warning_id="WARN-EXPIRED-1",
            authority=WarningAuthority.DGRE.value,
            hazard_type=HazardType.AVALANCHE.value,
            location_id="JK-SGR-01",
            severity_label="Yellow",
            headline="Past Avalanche Advisory",
            geographic_scope="Gulmarg Sector",
            summary="Moderate slide risk in past window.",
            advisory_notes="Advisory concluded.",
            source_url="https://dgre.drdo.gov.in/warn/exp",
            source_reference="DGRE Historical Record",
            issued_at=NOW - timedelta(days=5),
            valid_until=NOW - timedelta(days=2),
            is_read_only=True,
            provenance="official:dgre-exp",
            is_demo_fixture=True,
            ingested_at=NOW,
        )
    )

    session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[_get_db] = override_get_db
    yield session
    app.dependency_overrides.pop(_get_db, None)
    session.close()
    engine.dispose()


def test_unauthenticated_request_rejected() -> None:
    resp = client.get("/warnings")
    assert resp.status_code == 401


def test_viewer_can_read_warnings_list_and_details() -> None:
    token = create_access_token("viewer_user", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/warnings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["pagination"]["has_next"] is False

    # Get specific active warning
    resp_detail = client.get("/warnings/WARN-ACTIVE-1", headers=headers)
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["warning_id"] == "WARN-ACTIVE-1"
    assert detail["authority"] == "CWC"
    assert detail["severity_label"] == "Red"
    assert detail["is_read_only"] is True
    assert detail["is_expired"] is False
    assert detail["source_reference"] == "CWC Bulletin #1"
    assert detail["source_url"] == "https://cwc.gov.in/warn/1"


def test_warning_not_found_returns_404_envelope() -> None:
    token = create_access_token("viewer_user", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/warnings/NON_EXISTENT", headers=headers)
    assert resp.status_code == 404
    body = resp.json()
    assert body["error_code"] == "HTTP_404"
    assert "not found" in body["message"].lower()


def test_viewer_role_cannot_create_warning() -> None:
    """Ordinary roles (viewer) are read-only and forbidden from mutating warnings."""
    token = create_access_token("viewer_user", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "warning_id": "WARN-NEW-01",
        "authority": "IMD",
        "hazard_type": "flood",
        "location_id": "JK-SGR-01",
        "severity_label": "Orange",
        "headline": "Unauthorized Attempt",
        "issued_at": NOW.isoformat(),
        "valid_until": (NOW + timedelta(hours=8)).isoformat(),
        "provenance": "official:test",
    }
    resp = client.post("/warnings", json=payload, headers=headers)
    assert resp.status_code == 403


def test_operator_can_create_warning() -> None:
    """Operators have permission to ingest and curate warnings."""
    token = create_access_token("operator_user", "district_operator")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "warning_id": "WARN-OPERATOR-01",
        "authority": "IMD",
        "hazard_type": "flood",
        "location_id": "JK-SGR-01",
        "severity_label": "Orange",
        "headline": "Operator Curated Weather Alert",
        "geographic_scope": "Srinagar & Budgam",
        "summary": "Heavy rainfall warning.",
        "advisory_notes": "Monitor nallah gauges.",
        "source_url": "https://mausam.imd.gov.in/srinagar",
        "source_reference": "IMD MC Srinagar Nowcast #88",
        "issued_at": NOW.isoformat(),
        "valid_until": (NOW + timedelta(hours=8)).isoformat(),
        "provenance": "official:imd-88",
        "is_demo_fixture": False,
    }
    resp = client.post("/warnings", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["warning_id"] == "WARN-OPERATOR-01"
    assert data["is_read_only"] is True


def test_filtering_by_expiration_and_authority() -> None:
    token = create_access_token("viewer_user", "viewer")
    headers = {"Authorization": f"Bearer {token}"}

    # Filter active only
    resp = client.get("/warnings?is_expired=false", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["warning_id"] == "WARN-ACTIVE-1"

    # Filter expired only
    resp_exp = client.get("/warnings?is_expired=true", headers=headers)
    assert resp_exp.status_code == 200
    data_exp = resp_exp.json()
    assert data_exp["total"] == 1
    assert data_exp["items"][0]["warning_id"] == "WARN-EXPIRED-1"

    # Filter authority
    resp_auth = client.get("/warnings?authority=CWC", headers=headers)
    assert resp_auth.status_code == 200
    assert resp_auth.json()["total"] == 1
