"""Tests for authentication and role-based authorization."""

from datetime import timedelta
from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.user import UserModel, UserRole

BACKEND_DIR = Path(__file__).resolve().parents[2]
client = TestClient(app)


def _setup_auth_db(tmp_path: Path) -> None:
    """Apply migrations and seed a test user."""
    db_url = f"sqlite:///{tmp_path / 'auth.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session = get_session_factory(engine)()
    session.add(
        UserModel(
            user_id="test-admin-1",
            username="testadmin",
            hashed_password=hash_password("secret1234"),
            full_name="Test Admin",
            role=UserRole.ADMIN,
        )
    )
    session.add(
        UserModel(
            user_id="test-viewer-1",
            username="testviewer",
            hashed_password=hash_password("viewpass1234"),
            full_name="Test Viewer",
            role=UserRole.VIEWER,
        )
    )
    session.commit()
    session.close()
    engine.dispose()


def test_password_hash_not_reversible() -> None:
    hashed = hash_password("my_secret")
    assert hashed != "my_secret"
    assert verify_password("my_secret", hashed)
    assert not verify_password("wrong_password", hashed)


def test_valid_login_returns_token() -> None:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_bad_credentials_rejected() -> None:
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_missing_token_gets_401() -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_expired_token_gets_401() -> None:
    token = create_access_token("admin", "admin", expires_delta=timedelta(seconds=-1))
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_valid_token_returns_current_user() -> None:
    login_resp = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    token = login_resp.json()["access_token"]
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin"
    assert me_resp.json()["role"] == "admin"


def test_insufficient_role_gets_403() -> None:
    login_resp = client.post(
        "/auth/login",
        json={"username": "viewer", "password": "viewer1234"},
    )
    token = login_resp.json()["access_token"]
    # Forged X-User-Role header without JWT must be rejected
    forged_resp = client.post(
        "/locations",
        json={
            "location_id": "JK-ROLE-01",
            "name": "Role Test",
            "admin_unit": "Test District",
            "latitude": 34.0,
            "longitude": 75.0,
        },
        headers={"X-User-Role": "admin"},
    )
    assert forged_resp.status_code == 401

    # Viewers should be forbidden from creating locations (admin-only)
    response = client.post(
        "/locations",
        json={
            "location_id": "JK-ROLE-01",
            "name": "Role Test",
            "admin_unit": "Test District",
            "latitude": 34.0,
            "longitude": 75.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
