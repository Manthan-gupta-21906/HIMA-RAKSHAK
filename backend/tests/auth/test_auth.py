"""Tests for authentication, environment-only demo seeding, and role-based authorization."""

from collections.abc import Generator
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.user import UserModel, UserRole

BACKEND_DIR = Path(__file__).resolve().parents[2]
client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolated_auth_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None, None, None]:
    """Provide an isolated SQLite DB with ephemeral test accounts for each auth test."""
    db_url = f"sqlite:///{tmp_path / 'auth.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    factory = get_session_factory(engine)
    session = factory()
    session.add_all(
        [
            UserModel(
                user_id="test-admin-1",
                username="testadmin",
                hashed_password=hash_password("test-admin-pass"),
                full_name="Test Admin",
                role=UserRole.ADMIN,
                is_demo_fixture=False,
            ),
            UserModel(
                user_id="test-operator-1",
                username="testoperator",
                hashed_password=hash_password("test-operator-pass"),
                full_name="Test Operator",
                role=UserRole.DISTRICT_OPERATOR,
                is_demo_fixture=False,
            ),
            UserModel(
                user_id="test-viewer-1",
                username="testviewer",
                hashed_password=hash_password("test-viewer-pass"),
                full_name="Test Viewer",
                role=UserRole.VIEWER,
                is_demo_fixture=False,
            ),
            UserModel(
                user_id="test-disabled-1",
                username="disableduser",
                hashed_password=hash_password("test-disabled-pass"),
                full_name="Disabled User",
                role=UserRole.VIEWER,
                is_active=False,
                is_demo_fixture=False,
            ),
        ]
    )
    session.commit()
    session.close()

    monkeypatch.setattr(auth_routes, "_get_db", lambda: factory())
    try:
        yield
    finally:
        engine.dispose()


def test_password_hash_not_reversible() -> None:
    hashed = hash_password("my_secret")
    assert hashed != "my_secret"
    assert verify_password("my_secret", hashed)
    assert not verify_password("wrong_password", hashed)


@pytest.mark.parametrize(
    ("username", "password", "expected_role"),
    [
        ("testadmin", "test-admin-pass", "admin"),
        ("testoperator", "test-operator-pass", "district_operator"),
        ("testviewer", "test-viewer-pass", "viewer"),
    ],
)
def test_valid_login_returns_token_and_authoritative_role(
    username: str, password: str, expected_role: str
) -> None:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == username
    assert me_resp.json()["role"] == expected_role


def test_bad_credentials_rejected() -> None:
    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_disabled_account_rejected_with_403() -> None:
    response = client.post(
        "/auth/login",
        json={"username": "disableduser", "password": "test-disabled-pass"},
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_missing_token_gets_401() -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_expired_token_gets_401() -> None:
    token = create_access_token("testadmin", "admin", expires_delta=timedelta(seconds=-1))
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_insufficient_role_gets_403() -> None:
    login_resp = client.post(
        "/auth/login",
        json={"username": "testviewer", "password": "test-viewer-pass"},
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


def test_seed_demo_users_requires_env_passwords(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dev_settings_no_pw = Settings(
        app_env="development",
        jwt_secret_key="d" * 32,
        _env_file=None,
    )
    monkeypatch.setattr(auth_routes, "get_settings", lambda: dev_settings_no_pw)

    db_url = f"sqlite:///{tmp_path / 'seed_none.db'}"
    engine = create_db_engine(db_url)
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory(engine)

    with factory() as db:
        assert auth_routes.seed_demo_users(db) == 0
        assert db.query(UserModel).count() == 0

    dev_settings_with_pw = Settings(
        app_env="development",
        jwt_secret_key="d" * 32,
        demo_admin_password="env-admin-secret-value",
        _env_file=None,
    )
    monkeypatch.setattr(auth_routes, "get_settings", lambda: dev_settings_with_pw)
    with factory() as db:
        assert auth_routes.seed_demo_users(db) == 1
        seeded = db.query(UserModel).filter(UserModel.username == "Admin").first()
        assert seeded is not None
        assert verify_password("env-admin-secret-value", seeded.hashed_password)
    engine.dispose()


def test_production_never_seeds_demo_users_on_login(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prod_settings = Settings(
        app_env="production",
        jwt_secret_key="p" * 32,
        demo_admin_password="env-admin-secret-value",
        _env_file=None,
    )
    monkeypatch.setattr(auth_routes, "get_settings", lambda: prod_settings)

    db_url = f"sqlite:///{tmp_path / 'prod_auth.db'}"
    prod_engine = create_db_engine(db_url)
    Base.metadata.create_all(bind=prod_engine)
    prod_factory = get_session_factory(prod_engine)
    monkeypatch.setattr(auth_routes, "_get_db", lambda: prod_factory())

    with prod_factory() as db:
        assert auth_routes.seed_demo_users(db) == 0
        assert db.query(UserModel).count() == 0

    resp = client.post(
        "/auth/login",
        json={"username": "Admin", "password": "env-admin-secret-value"},
    )
    assert resp.status_code == 401

    with prod_factory() as db_check:
        assert db_check.query(UserModel).count() == 0
    prod_engine.dispose()
