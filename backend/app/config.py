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
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"
    demo_admin_username: str = "Admin"
    demo_admin_password: str | None = None
    demo_operator_username: str = "operator"
    demo_operator_password: str | None = None
    demo_viewer_username: str = "viewer"
    demo_viewer_password: str | None = None
    alert_webhook_url: str | None = None
    alert_webhook_timeout_seconds: float = 5.0
    alert_smtp_host: str | None = None
    alert_smtp_port: int = 587
    alert_smtp_from: str | None = None
    alert_email_recipients: str = ""
    ingestion_scheduler_enabled: bool = False
    ingestion_poll_interval_seconds: int = 60
    ingestion_max_retries: int = 3
    ingestion_retry_backoff_seconds: float = 2.0

    @property
    def cors_origin_list(self) -> list[str]:
        """Return explicit, non-wildcard allowed CORS origins."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip() and origin.strip() != "*"
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_jwt_secret(self) -> "Settings":
        """Require JWT_SECRET_KEY from environment and reject default or weak secrets."""
        secret = self.jwt_secret_key.strip()
        if secret in _INSECURE_DEFAULT_SECRETS:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a non-default secret via environment variables."
            )
        if self.app_env.lower() not in {"development", "test"} and len(secret) < _MIN_SECRET_LENGTH:
            raise ValueError(
                "JWT_SECRET_KEY must be a non-default secret of at least 32 characters "
                "outside development/test environments."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
