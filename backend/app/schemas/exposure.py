"""Domain schemas for spatial exposure, critical assets, and priority indexing."""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import AwareDatetime, RiskClass


class ExposureCoverageStatus(StrEnum):
    """Data coverage completeness for exposure assets."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ExposureCountType(StrEnum):
    """Distinction between verified counts and model/spatial estimates."""

    VERIFIED = "verified"
    ESTIMATED = "estimated"


class ExposureAsset(BaseModel):
    """An exposed element (settlement, road, home, critical infrastructure)."""

    asset_id: str
    asset_type: str  # e.g., "settlement", "road", "home", "critical_facility"
    name: str
    count: int = 1
    count_type: ExposureCountType = ExposureCountType.ESTIMATED
    population_affected: int = 0
    is_critical: bool = False
    metadata: dict[str, str | float | int | bool] = Field(default_factory=dict)


class LocationExposureProfile(BaseModel):
    """Spatial intersection summary of assets located within a risk zone."""

    location_id: str
    evaluated_at: AwareDatetime
    coverage_status: ExposureCoverageStatus
    population_exposed: int = 0
    settlements_count: int = 0
    homes_exposed: int = 0
    roads_exposed_km: float = 0.0
    critical_facilities_count: int = 0
    assets: list[ExposureAsset] = Field(default_factory=list)
    missing_layers: list[str] = Field(default_factory=list)


class PriorityAssessment(BaseModel):
    """Decision support priority score and ranking for civil defense and emergency response."""

    location_id: str
    evaluated_at: AwareDatetime
    hazard_score: float | None = None
    hazard_risk_class: RiskClass
    exposure_score: float = Field(ge=0.0, le=1.0)
    impact_score: float = Field(ge=0.0, le=1.0)
    priority_score: float = Field(ge=0.0, le=1.0)
    coverage_status: ExposureCoverageStatus
    priority_level: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    weights_used: dict[str, float]
    breakdown: dict[str, float]
