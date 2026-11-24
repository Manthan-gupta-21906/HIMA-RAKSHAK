"""Stable API error envelope and error detail contracts."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.schemas.common import AwareDatetime


class ErrorDetail(BaseModel):
    """Field-level or contextual error detail."""

    field: str | None = None
    code: str = Field(..., min_length=2, max_length=64)
    message: str = Field(..., min_length=1, max_length=300)


class ErrorEnvelope(BaseModel):
    """Standardized API error response envelope."""

    error_code: str = Field(..., min_length=2, max_length=64)
    message: str = Field(..., min_length=1, max_length=300)
    details: list[ErrorDetail] = Field(default_factory=list)
    timestamp: AwareDatetime


def build_error_envelope(
    error_code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> ErrorEnvelope:
    """Create a UTC-timestamped ErrorEnvelope."""
    return ErrorEnvelope(
        error_code=error_code,
        message=message,
        details=details or [],
        timestamp=datetime.now(UTC),
    )
