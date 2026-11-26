"""Tests for configurable CORS preflight and authenticated cross-origin requests."""

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def test_cors_preflight_allows_configured_origin() -> None:
    response = client.options(
        "/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_preflight_blocks_disallowed_origin() -> None:
    response = client.options(
        "/auth/me",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") is None


def test_authenticated_request_includes_cors_header_for_allowed_origin() -> None:
    token = create_access_token("operator", "district_operator")
    response = client.get(
        "/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Authorization": f"Bearer {token}",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
