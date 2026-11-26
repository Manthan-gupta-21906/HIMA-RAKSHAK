"""Observation contracts with metric-to-unit validation and creation schemas."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.schemas.common import AwareDatetime, HazardType, PaginationMeta


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


def normalize_unit_and_value(
    metric: ObservationMetric, raw_value: float, raw_unit: str
) -> tuple[float, str]:
    """Normalize common unit variants to canonical metric units."""
    unit = raw_unit.strip().lower()
    expected = ALLOWED_UNITS[metric]
    if raw_unit.strip() == expected:
        return raw_value, expected

    if metric == ObservationMetric.SNOW_DEPTH_CM:
        if unit in {"cm", "cm snow"}:
            return raw_value, "cm"
        if unit == "mm":
            return round(raw_value / 10.0, 4), "cm"
        if unit in {"m", "meter", "meters"}:
            return round(raw_value * 100.0, 4), "cm"
        if unit in {"in", "inch", "inches"}:
            return round(raw_value * 2.54, 4), "cm"
    elif metric == ObservationMetric.RIVER_LEVEL_M:
        if unit in {"m", "meter", "meters"}:
            return raw_value, "m"
        if unit in {"ft", "feet", "ft water"}:
            return round(raw_value * 0.3048, 4), "m"
    elif metric == ObservationMetric.RAIN_MM:
        if unit in {"mm", "mm rain"}:
            return raw_value, "mm"
        if unit == "cm":
            return round(raw_value * 10.0, 4), "mm"
        if unit in {"in", "inch", "inches"}:
            return round(raw_value * 25.4, 4), "mm"
    elif metric == ObservationMetric.TEMP_C:
        if unit in {"c", "degc", "°c"}:
            return raw_value, "C"
        if unit in {"f", "degf", "°f"}:
            return round((raw_value - 32.0) * 5.0 / 9.0, 4), "C"
    elif metric == ObservationMetric.WIND_KMH:
        if unit in {"km/h", "kmh", "kph"}:
            return raw_value, "km/h"
        if unit in {"m/s", "mps"}:
            return round(raw_value * 3.6, 4), "km/h"
        if unit in {"mph", "mi/h"}:
            return round(raw_value * 1.60934, 4), "km/h"

    return raw_value, raw_unit.strip()


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


class ObservationCreate(BaseModel):
    """Payload to record an authenticated field or telemetry observation."""

    location_id: str = Field(
        ...,
        min_length=2,
        max_length=32,
        description="Target location identifier",
        validation_alias=AliasChoices("location_id", "sector_id"),
    )
    hazard_type: HazardType | None = Field(
        default=None, description="Associated hazard pathway"
    )
    metric: ObservationMetric | None = Field(
        default=None, description="Observed environmental metric"
    )
    value: float = Field(..., description="Observed numeric value")
    unit: str = Field(
        ..., min_length=1, max_length=16, description="Measurement unit"
    )
    observed_at: AwareDatetime | None = Field(
        default=None, description="Observation timestamp (ISO 8601 with timezone)"
    )
    source_id: str | None = Field(
        default="src-field-obs", max_length=64, description="Originating source identifier"
    )
    notes: str | None = Field(
        default=None, max_length=1000, description="Field notes or context"
    )

    @model_validator(mode="after")
    def validate_observation(self) -> "ObservationCreate":
        # 1. Resolve metric from hazard_type if omitted
        if self.metric is None:
            if self.hazard_type == HazardType.AVALANCHE:
                self.metric = ObservationMetric.SNOW_DEPTH_CM
            elif self.hazard_type == HazardType.FLOOD:
                self.metric = ObservationMetric.RIVER_LEVEL_M
            else:
                raise ValueError(
                    "Either 'metric' or a supported 'hazard_type' must be specified."
                )

        # 2. Check hazard pathway compatibility if provided
        if self.hazard_type is not None:
            compatible: dict[HazardType, set[ObservationMetric]] = {
                HazardType.FLOOD: {
                    ObservationMetric.RAIN_MM,
                    ObservationMetric.RIVER_LEVEL_M,
                    ObservationMetric.TEMP_C,
                },
                HazardType.AVALANCHE: {
                    ObservationMetric.SNOW_DEPTH_CM,
                    ObservationMetric.WIND_KMH,
                    ObservationMetric.TEMP_C,
                },
            }
            if self.metric not in compatible.get(self.hazard_type, set()):
                raise ValueError(
                    f"Metric '{self.metric.value}' is incompatible with hazard pathway "
                    f"'{self.hazard_type.value}'."
                )

        # 3. Normalize unit and value
        norm_val, norm_unit = normalize_unit_and_value(self.metric, self.value, self.unit)
        expected_unit = ALLOWED_UNITS[self.metric]
        if norm_unit != expected_unit:
            raise ValueError(
                f"Invalid unit '{self.unit}' for metric '{self.metric.value}'. "
                f"Expected '{expected_unit}'."
            )
        self.value = norm_val
        self.unit = norm_unit

        # 4. Physical bounds check (negative check for non-temperature)
        if self.metric != ObservationMetric.TEMP_C and self.value < 0.0:
            raise ValueError(
                f"Physical measurement for '{self.metric.value}' cannot be negative."
            )

        bounds: dict[ObservationMetric, tuple[float, float]] = {
            ObservationMetric.RAIN_MM: (0.0, 2000.0),
            ObservationMetric.RIVER_LEVEL_M: (0.0, 100.0),
            ObservationMetric.SNOW_DEPTH_CM: (0.0, 2000.0),
            ObservationMetric.WIND_KMH: (0.0, 400.0),
            ObservationMetric.TEMP_C: (-70.0, 70.0),
        }
        min_val, max_val = bounds[self.metric]
        if self.value < min_val or self.value > max_val:
            raise ValueError(
                f"Value {self.value} {self.unit} is outside allowable range "
                f"[{min_val}, {max_val}] for '{self.metric.value}'."
            )

        # 5. Timestamp validation
        now = datetime.now(UTC)
        if self.observed_at is None:
            self.observed_at = now
        else:
            if self.observed_at > now + timedelta(minutes=5):
                raise ValueError("Observation timestamp cannot be in the future.")
            if self.observed_at < now - timedelta(days=365):
                raise ValueError("Observation timestamp cannot be older than 1 year.")

        return self


class ObservationListResponse(BaseModel):
    """Paginated list of environmental observations."""

    total: int
    items: list[ObservationContract]
    pagination: PaginationMeta | None = None
