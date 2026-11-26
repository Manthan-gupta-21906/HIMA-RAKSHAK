"""Observation contracts with metric-to-unit validation."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import AwareDatetime, PaginationMeta


class ObservationMetric(StrEnum):
    """Supported environmental observation metrics."""

    RAIN_MM = "rain_mm"
    RIVER_LEVEL_M = "river_level_m"
    SNOW_DEPTH_CM = "snow_depth_cm"
    WIND_KMH = "wind_kmh"
    TEMP_C = "temp_c"


ALLOWED_UNITS: dict[ObservationMetric, str] = {
    ObservationMetric.RAIN_MM: "mm",
    ObservationMetric.RIVER_LEVEL_M: "m",
    ObservationMetric.SNOW_DEPTH_CM: "cm",
    ObservationMetric.WIND_KMH: "km/h",
    ObservationMetric.TEMP_C: "C",
}


class ObservationContract(BaseModel):
    """Validated environmental observation tied to a location and source."""

    observation_id: str = Field(..., min_length=2, max_length=64)
    location_id: str = Field(..., min_length=3, max_length=32)
    source_id: str = Field(..., min_length=2, max_length=64)
    observed_at: AwareDatetime
    metric: ObservationMetric
    value: float
    unit: str = Field(..., min_length=1, max_length=16)
    is_demo_fixture: bool = True

    @model_validator(mode="after")
    def validate_unit_matches_metric(self) -> "ObservationContract":
        expected = ALLOWED_UNITS[self.metric]
        if self.unit != expected:
            msg = f"Invalid unit '{self.unit}' for '{self.metric.value}'; expected '{expected}'."
            raise ValueError(msg)
        return self


class ObservationListResponse(BaseModel):
    """Paginated list of environmental observations."""

    total: int
    items: list[ObservationContract]
    pagination: PaginationMeta | None = None
