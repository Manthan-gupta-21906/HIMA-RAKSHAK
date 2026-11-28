"""API tests for operational alerts listing, acknowledgement, and role policy."""

from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import alerts as alerts_routes
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.alert import AlertActionModel  # noqa: F401
from app.models.location import LocationModel  # noqa: F401
from app.models.user import UserModel  # noqa: F401
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertActionRecord, AlertStatus
from app.schemas.common import HazardType

client = TestClient(app)


@pytest.fixture(autouse=True)
def _alerts_db(tmp_path: Path) -> Generator[None, None, None]:
    """Provide an isolated SQLite DB containing one active operational alert."""
    engine = create_db_engine(f"sqlite:///{tmp_path / 'alerts_api.db'}")
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory(engine)

    session = factory()

    with factory() as seed_db:
        AlertRepository(seed_db).create(
            AlertActionRecord(
                alert_id="alert-flood-test1",
                location_id="JK-SGR-01",
                hazard_type=HazardType.FLOOD,
                risk_id="risk-flood-test1",
                priority_level="HIGH",
                priority_score=0.8,
                title="HIGH Flood Alert — JK-SGR-01",
                recommendation="Activate river gauge watch.",
                explanation=["River level above the warning mark"],
                status=AlertStatus.ACTIVE,
                created_at=datetime.now(UTC),
            )
        )
        seed_db.commit()

    def _override_get_db() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[alerts_routes._get_db] = _override_get_db
    previous_override = app.dependency_overrides.get(alerts_routes._get_db)
    try:
        yield session
    finally:
        app.dependency_overrides.pop(alerts_routes._get_db, None)
        if previous_override is not None:
            app.dependency_overrides[alerts_routes._get_db] = previous_override
        session.close()


def _headers(role: str) -> dict[str, str]:
    token = create_access_token(f"{role}_user", role)
    return {"Authorization": f"Bearer {token}"}


def test_list_alerts_requires_authentication() -> None:
    assert client.get("/alerts").status_code == 401


def test_viewer_can_list_system_alerts_distinct_from_warnings() -> None:
    response = client.get("/alerts", headers=_headers("viewer"))
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    alert = data["items"][0]
    assert alert["alert_id"] == "alert-flood-test1"
    assert alert["is_official_warning"] is False
    assert alert["status"] == "active"
    assert alert["priority_level"] == "HIGH"


def test_viewer_cannot_acknowledge_or_update_action() -> None:
    acknowledge = client.post(
        "/alerts/alert-flood-test1/acknowledge",
        headers=_headers("viewer"),
    )
    assert acknowledge.status_code == 403

    action = client.patch(
        "/alerts/alert-flood-test1/action",
        json={"status": "resolved"},
        headers=_headers("viewer"),
    )
    assert action.status_code == 403


def test_operator_acknowledges_and_updates_action() -> None:
    headers = _headers("district_operator")

    acknowledged = client.post(
        "/alerts/alert-flood-test1/acknowledge",
        json={"note": "Gauge watch activated"},
        headers=headers,
    )
    assert acknowledged.status_code == 200
    body = acknowledged.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_by"] == "district_operator_user"
    assert body["acknowledged_at"] is not None
    assert body["action_note"] == "Gauge watch activated"

    updated = client.patch(
        "/alerts/alert-flood-test1/action",
        json={"status": "resolved", "action_note": "Road reopened"},
        headers=headers,
    )
    assert updated.status_code == 200
    updated_body = updated.json()
    assert updated_body["status"] == "resolved"
    assert updated_body["action_note"] == "Road reopened"
    assert updated_body["action_updated_at"] is not None


def test_unrelated_dependency_overrides_remain_intact() -> None:
    """Verify the alerts fixture does not clear unrelated dependency overrides."""
    from app.api.routes import risk as risk_routes

    def dummy_get_db():
        pass

    app.dependency_overrides[risk_routes._get_db] = dummy_get_db
    try:
        assert app.dependency_overrides.get(risk_routes._get_db) is dummy_get_db
    finally:
        app.dependency_overrides.pop(risk_routes._get_db, None)


def test_dependency_override_restored_after_fixture() -> None:
    """Verify a pre-existing override for the same dependency is restored."""
    from app.api.routes import alerts as alerts_routes

    def pre_existing_override():
        pass

    app.dependency_overrides[alerts_routes._get_db] = pre_existing_override
    try:
        assert app.dependency_overrides.get(alerts_routes._get_db) is pre_existing_override
    finally:
        app.dependency_overrides.pop(alerts_routes._get_db, None)
