"""Minimum evidentiary thresholds and requirement specifications for avalanche readiness."""

from pydantic import BaseModel


class AvalancheRequirements(BaseModel):
    """Scientific evidentiary thresholds required for validated avalanche forecasting."""

    min_historical_event_labels: int = 10
    min_historical_non_event_labels: int = 10
    max_snowpack_staleness_hours: int = 24
    require_snowpack_telemetry: bool = True
    require_terrain_coverage: bool = True
    require_wind_loading: bool = True
    require_temperature_trend: bool = True


DEFAULT_AVALANCHE_REQUIREMENTS = AvalancheRequirements()


# Stable reason messages for auditability and consistent UI presentation
REASON_MISSING_SNOWPACK = "Snowpack telemetry (snow depth / new snow) is missing."
REASON_STALE_SNOWPACK = "Snowpack observations are stale (>24h old); cannot validate current layer."
REASON_TERRAIN_ONLY = (
    "Terrain-only inputs (slope/aspect/elevation) cannot produce a validated forecast."
)
REASON_MISSING_EVENT_LABELS = (
    "Verified historical avalanche occurrence labels are unavailable or insufficient."
)
REASON_MISSING_TERRAIN = "Terrain morphology attributes (slope, aspect, elevation) are missing."
REASON_MISSING_METEOROLOGY = "Meteorological telemetry (temperature or wind loading) is missing."
REASON_STALE_METEOROLOGY = "Meteorological observations are stale."
