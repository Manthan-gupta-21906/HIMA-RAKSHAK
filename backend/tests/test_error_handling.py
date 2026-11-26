"""Tests for global 500 exception handling without sensitive detail leakage."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_unhandled_exception_returns_safe_error_envelope() -> None:
    app = create_app()

    @app.get("/_test-crash")
    def crash_route() -> None:
        raise RuntimeError("sensitive_db_password_leaked")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test-crash")

    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "INTERNAL_ERROR"
    assert body["message"] == "An unexpected internal error occurred."
    assert body["details"] == []
    assert "timestamp" in body
    assert "sensitive_db_password_leaked" not in response.text
    assert "Traceback" not in response.text
