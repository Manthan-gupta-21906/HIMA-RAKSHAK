"""Tests for runtime configuration and JWT secret validation."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_allows_default_secret_in_development_and_test() -> None:
    dev = Settings(app_env="development", _env_file=None)
    test = Settings(app_env="test", _env_file=None)
    assert dev.jwt_secret_key == "change-me-in-local-env"
    assert test.jwt_secret_key == "change-me-in-local-env"


@pytest.mark.parametrize(
    "bad_secret",
    ["", "change-me-in-local-env", "short-secret-under-32-chars"],
)
def test_settings_rejects_weak_or_default_secret_in_production(bad_secret: str) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env="production", jwt_secret_key=bad_secret, _env_file=None)


def test_settings_accepts_strong_secret_in_production() -> None:
    strong = "a" * 32
    prod = Settings(app_env="production", jwt_secret_key=strong, _env_file=None)
    assert prod.jwt_secret_key == strong
