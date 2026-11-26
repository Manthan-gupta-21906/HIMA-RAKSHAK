"""Tests for runtime configuration and environment-only secret validation."""

import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize("env_name", ["development", "test", "production"])
def test_settings_requires_jwt_secret_from_env(
    env_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env=env_name, _env_file=None)


@pytest.mark.parametrize(
    "bad_secret",
    ["", "   ", "change-me-in-local-env", "change_me_local_only"],
)
@pytest.mark.parametrize("env_name", ["development", "test", "production"])
def test_settings_rejects_placeholder_or_empty_secret(
    env_name: str, bad_secret: str
) -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env=env_name, jwt_secret_key=bad_secret, _env_file=None)


def test_settings_rejects_short_secret_in_production() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(
            app_env="production",
            jwt_secret_key="short-secret-under-32-chars",
            _env_file=None,
        )


def test_settings_accepts_env_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    strong = "a" * 32
    monkeypatch.setenv("JWT_SECRET_KEY", strong)
    for env_name in ("development", "test", "production"):
        cfg = Settings(app_env=env_name, _env_file=None)
        assert cfg.jwt_secret_key == strong
