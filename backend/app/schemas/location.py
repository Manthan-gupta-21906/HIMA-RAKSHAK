"""Pydantic schemas for the pilot location catalogue API."""

from pydantic import BaseModel, Field

from app.models.location import CoverageStatus, HazardType


class LocationOut(BaseModel):
    """Public representation of a pilot location."""

    location_id: str
    name: str
    admin_unit: str
    latitude: float
    longitude: float
    geometry_geojson: dict[str, object]
    supported_hazards: list[HazardType]
    coverage_status: CoverageStatus
    coverage_note: str
    is_demo_fixture: bool
    provenance: str


class LocationListResponse(BaseModel):
    """Paginated/filtered list of pilot locations."""

    total: int
    items: list[LocationOut]


class LocationCreate(BaseModel):
    """Payload to register a pilot location (admin only)."""

    location_id: str = Field(..., min_length=3, max_length=32)
    name: str = Field(..., min_length=2, max_length=120)
    admin_unit: str = Field(..., min_length=2, max_length=120)
    latitude: float = Field(..., ge=32.0, le=37.5)
    longitude: float = Field(..., ge=72.5, le=80.5)
    supported_hazards: list[HazardType] = Field(default_factory=list)
    coverage_status: CoverageStatus = "partial"
    coverage_note: str = Field(default="Indicative pilot entry pending local validation.")


class LocationCoverageUpdate(BaseModel):
    """Payload to update coverage status for a location (admin only)."""

    coverage_status: CoverageStatus
    coverage_note: str = Field(..., min_length=3, max_length=300)
