"""Tests for the system health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "HIMA-RAKSHAK"
    assert payload["version"] == "0.1.0"
    assert "environment" in payload
