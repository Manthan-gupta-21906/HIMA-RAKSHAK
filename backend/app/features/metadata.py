"""Feature definitions, provenance containers, and terrain context."""

from pydantic import BaseModel, Field

from app.schemas.common import FreshnessStatus, HazardType


class FeatureDefinition(BaseModel):
    """Documented metadata for a single engineered feature."""

    name: str
    hazard_type: HazardType
    unit: str
    window_hours: int | None = None
    description: str


class FeatureValue(BaseModel):
    """Computed feature value with missingness, freshness, and source provenance."""

    name: str
    value: float | None = None
    unit: str
    window_hours: int | None = None
    is_missing: bool
    source_ids: list[str] = Field(default_factory=list)
    freshness: FreshnessStatus = FreshnessStatus.UNKNOWN


class TerrainContext(BaseModel):
    """Optional static GIS/terrain attributes for a location."""

    elevation_m: float | None = None
    slope_deg: float | None = Field(default=None, ge=0.0, le=90.0)
    aspect_deg: float | None = Field(default=None, ge=0.0, le=360.0)
    drainage_density: float | None = Field(default=None, ge=0.0)


FLOOD_FEATURE_SPECS: dict[str, FeatureDefinition] = {
    "rain_1h_mm": FeatureDefinition(
        name="rain_1h_mm",
        hazard_type=HazardType.FLOOD,
        unit="mm",
        window_hours=1,
        description="Cumulative rainfall in the 1h window ending at cutoff.",
    ),
    "rain_24h_mm": FeatureDefinition(
        name="rain_24h_mm",
        hazard_type=HazardType.FLOOD,
        unit="mm",
        window_hours=24,
        description="Cumulative rainfall in the 24h window ending at cutoff.",
    ),
    "antecedent_rain_72h_mm": FeatureDefinition(
        name="antecedent_rain_72h_mm",
        hazard_type=HazardType.FLOOD,
        unit="mm",
        window_hours=72,
        description="Antecedent rainfall from 72h to 24h before cutoff.",
    ),
    "river_level_m": FeatureDefinition(
        name="river_level_m",
        hazard_type=HazardType.FLOOD,
        unit="m",
        window_hours=24,
        description="Latest river stage gauge reading within 24h of cutoff.",
    ),
    "river_level_rate_m_per_h": FeatureDefinition(
        name="river_level_rate_m_per_h",
        hazard_type=HazardType.FLOOD,
        unit="m/h",
        window_hours=6,
        description="River level rate of rise over the 6h window ending at cutoff.",
    ),
    "drainage_density": FeatureDefinition(
        name="drainage_density",
        hazard_type=HazardType.FLOOD,
        unit="km/km2",
        window_hours=None,
        description="Static catchment drainage density where GIS terrain is available.",
    ),
}

AVALANCHE_FEATURE_SPECS: dict[str, FeatureDefinition] = {
    "new_snow_24h_cm": FeatureDefinition(
        name="new_snow_24h_cm",
        hazard_type=HazardType.AVALANCHE,
        unit="cm",
        window_hours=24,
        description="Positive snow depth accumulation over the 24h window ending at cutoff.",
    ),
    "snow_depth_cm": FeatureDefinition(
        name="snow_depth_cm",
        hazard_type=HazardType.AVALANCHE,
        unit="cm",
        window_hours=24,
        description="Latest total snowpack depth within 24h of cutoff.",
    ),
    "swe_estimate_mm": FeatureDefinition(
        name="swe_estimate_mm",
        hazard_type=HazardType.AVALANCHE,
        unit="mm",
        window_hours=24,
        description="Indicative snow water equivalent (2.5 mm/cm) from latest snow depth.",
    ),
    "temp_mean_24h_c": FeatureDefinition(
        name="temp_mean_24h_c",
        hazard_type=HazardType.AVALANCHE,
        unit="C",
        window_hours=24,
        description="Mean air temperature over the 24h window ending at cutoff.",
    ),
    "wind_loading_kmh": FeatureDefinition(
        name="wind_loading_kmh",
        hazard_type=HazardType.AVALANCHE,
        unit="km/h",
        window_hours=24,
        description="Peak wind speed over the 24h window ending at cutoff.",
    ),
    "slope_deg": FeatureDefinition(
        name="slope_deg",
        hazard_type=HazardType.AVALANCHE,
        unit="deg",
        window_hours=None,
        description="Terrain slope angle in degrees.",
    ),
    "aspect_deg": FeatureDefinition(
        name="aspect_deg",
        hazard_type=HazardType.AVALANCHE,
        unit="deg",
        window_hours=None,
        description="Terrain aspect azimuth in degrees.",
    ),
    "elevation_m": FeatureDefinition(
        name="elevation_m",
        hazard_type=HazardType.AVALANCHE,
        unit="m",
        window_hours=None,
        description="Site elevation in meters above sea level.",
    ),
}
