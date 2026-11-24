"""Source provenance contracts."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    """Classification of environmental or warning data sources."""

    WEATHER = "weather"
    HYDROLOGY = "hydrology"
    SNOW = "snow"
    TERRAIN = "terrain"
    OFFICIAL_WARNING = "official_warning"
    FIELD_OBSERVATION = "field_observation"


class SourceContract(BaseModel):
    """Metadata describing an upstream or demo data source."""

    source_id: str = Field(..., min_length=2, max_length=64)
    source_name: str = Field(..., min_length=2, max_length=120)
    source_type: SourceType
    licence: str = Field(..., min_length=2, max_length=120)
    update_frequency_minutes: int = Field(..., ge=1, le=10080)
    is_authoritative: bool = False
    is_demo_fixture: bool = True
