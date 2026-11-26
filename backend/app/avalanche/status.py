"""Avalanche operational status definitions and explanation models."""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import AwareDatetime


class AvalancheOperationalStatus(StrEnum):
    """Operational avalanche readiness states according to evidence levels."""

    SUPPORTED = "supported"  # Full snowpack, fresh telemetry, terrain, and verified labels
    INDICATIVE_SCREENING = "indicative_screening"  # Screening heuristic only; unvalidated
    UNSUPPORTED = "unsupported"  # Insufficient or stale inputs to even screen reliably


class AvalancheReadinessAssessment(BaseModel):
    """Assessment output explaining why an avalanche evaluation attained a specific status."""

    location_id: str
    evaluated_at: AwareDatetime
    status: AvalancheOperationalStatus
    is_validated_forecast_allowed: bool
    reasons: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
