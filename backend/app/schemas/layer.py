"""Contracts for managed GIS layers."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import AwareDatetime


class LayerCategory(StrEnum):
    """Supported managed GIS layer categories."""

    EXPOSURE = "exposure"
    COVERAGE = "coverage"
    HAZARD_ZONE = "hazard_zone"


class ManagedLayerCreate(BaseModel):
    """Payload to register or update a managed GeoJSON GIS layer."""

    layer_id: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=120)
    layer_category: LayerCategory = LayerCategory.EXPOSURE
    description: str = Field(default="", max_length=500)
    provenance: str = Field(..., min_length=2, max_length=200)
    is_demo_fixture: bool = False
    geojson: dict[str, Any]


class ManagedLayerSummary(BaseModel):
    """Metadata summary for a managed GIS layer."""

    layer_id: str
    name: str
    layer_category: LayerCategory
    description: str
    provenance: str
    is_demo_fixture: bool
    source_crs_epsg: int
    feature_count: int
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ManagedLayerDetail(ManagedLayerSummary):
    """Full managed GIS layer including normalized EPSG:4326 GeoJSON."""

    geojson: dict[str, Any]


class ManagedLayerListResponse(BaseModel):
    """Response envelope for listing managed GIS layers."""

    total: int
    items: list[ManagedLayerSummary]
