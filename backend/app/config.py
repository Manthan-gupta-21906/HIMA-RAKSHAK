"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULT_SECRETS = {"", "change-me-in-local-env", "change_me_local_only"}
_MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Runtime configuration for the HIMA-RAKSHAK API."""

    app_name: str = "HIMA-RAKSHAK"
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./hima_rakshak.db"
    jwt_secret_key: str = "change-me-in-local-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> "Settings":
        """Reject default, empty, or short JWT secrets outside development and test."""
        if self.app_env.lower() not in {"development", "test"}:
            secret = self.jwt_secret_key.strip()
            if secret in _INSECURE_DEFAULT_SECRETS or len(secret) < _MIN_SECRET_LENGTH:
                raise ValueError(
                    "JWT_SECRET_KEY must be a non-default secret of at least 32 characters "
                    "outside development/test environments."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
