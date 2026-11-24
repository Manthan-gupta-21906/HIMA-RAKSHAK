"""Domain model for curated pilot locations."""

from dataclasses import dataclass, field
from typing import Literal

HazardType = Literal["flood", "avalanche"]
CoverageStatus = Literal["supported", "partial", "unsupported"]


@dataclass
class LocationRecord:
    """Pilot location entity with spatial coordinates, hazard support, and coverage."""

    location_id: str
    name: str
    admin_unit: str
    latitude: float
    longitude: float
    supported_hazards: list[HazardType]
    coverage_status: CoverageStatus
    coverage_note: str
    geometry_geojson: dict[str, object] = field(default_factory=dict)
    is_demo_fixture: bool = True
    provenance: str = "demo_fixture:round1_jk_pilot"
