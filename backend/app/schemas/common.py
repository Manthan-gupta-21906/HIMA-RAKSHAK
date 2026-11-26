"""Shared domain enums, timezone-aware timestamps, and provenance contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


def ensure_timezone_aware(value: datetime) -> datetime:
    """Reject naive datetimes lacking tzinfo or UTC offset."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must be timezone-aware.")
    return value


AwareDatetime = Annotated[datetime, AfterValidator(ensure_timezone_aware)]


class HazardType(StrEnum):
    """Supported hazard pathways."""

    FLOOD = "flood"
    AVALANCHE = "avalanche"


class RiskClass(StrEnum):
    """Discrete hazard risk classes."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    UNSUPPORTED = "unsupported"


class PredictionStatus(StrEnum):
    """Model and data readiness state for an assessment."""

    READY = "ready"
    INDICATIVE = "indicative"
    STALE = "stale"
    UNSUPPORTED = "unsupported"


class FreshnessStatus(StrEnum):
    """Freshness state of underlying observations."""

    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class ProvenanceMeta(BaseModel):
    """Provenance metadata attached to observations and assessments."""

    source_id: str = Field(..., min_length=2, max_length=64)
    source_name: str = Field(..., min_length=2, max_length=120)
    licence: str = Field(..., min_length=2, max_length=120)
    is_demo_fixture: bool = True
    ingested_at: AwareDatetime


class PaginationMeta(BaseModel):
    """Pagination metadata container."""

    total: int
    page: int
    page_size: int
    has_next: bool
