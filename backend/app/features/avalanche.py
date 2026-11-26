"""Avalanche hazard feature extraction pipeline."""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.features.common import (
    aggregate_overall_freshness,
    build_feature_value,
    filter_observations_in_window,
)
from app.features.metadata import AVALANCHE_FEATURE_SPECS, FeatureValue, TerrainContext
from app.schemas.common import AwareDatetime, FreshnessStatus, HazardType
from app.schemas.observation import ObservationContract, ObservationMetric

SWE_MM_PER_CM_RATIO = 2.5


class AvalancheFeatureVector(BaseModel):
    """Independent feature vector for the avalanche risk pathway."""

    hazard_type: Literal[HazardType.AVALANCHE] = HazardType.AVALANCHE
    location_id: str
    cutoff_at: AwareDatetime
    new_snow_24h_cm: FeatureValue
    snow_depth_cm: FeatureValue
    swe_estimate_mm: FeatureValue
    temp_mean_24h_c: FeatureValue
    wind_loading_kmh: FeatureValue
    slope_deg: FeatureValue
    aspect_deg: FeatureValue
    elevation_m: FeatureValue
    missing_count: int
    overall_freshness: FreshnessStatus


def extract_avalanche_features(
    location_id: str,
    observations: Sequence[ObservationContract],
    cutoff_at: datetime,
    terrain: TerrainContext | None = None,
    source_cadences: dict[str, int] | None = None,
) -> AvalancheFeatureVector:
    """Compute avalanche features strictly up to ``cutoff_at`` without future leakage."""
    snow_obs = filter_observations_in_window(
        observations,
        location_id,
        cutoff_at,
        metric=ObservationMetric.SNOW_DEPTH_CM,
        window_hours=24,
    )
    temp_obs = filter_observations_in_window(
        observations, location_id, cutoff_at, metric=ObservationMetric.TEMP_C, window_hours=24
    )
    wind_obs = filter_observations_in_window(
        observations, location_id, cutoff_at, metric=ObservationMetric.WIND_KMH, window_hours=24
    )

    new_snow_val: float | None = None
    if len(snow_obs) >= 2:
        new_snow_val = max(0.0, snow_obs[-1].value - snow_obs[0].value)

    latest_snow = snow_obs[-1].value if snow_obs else None
    swe_val = latest_snow * SWE_MM_PER_CM_RATIO if latest_snow is not None else None
    temp_mean = sum(o.value for o in temp_obs) / len(temp_obs) if temp_obs else None
    wind_max = max(o.value for o in wind_obs) if wind_obs else None

    f_new_snow = build_feature_value(
        AVALANCHE_FEATURE_SPECS["new_snow_24h_cm"],
        new_snow_val,
        snow_obs,
        cutoff_at,
        source_cadences,
    )
    f_snow_depth = build_feature_value(
        AVALANCHE_FEATURE_SPECS["snow_depth_cm"],
        latest_snow,
        snow_obs,
        cutoff_at,
        source_cadences,
    )
    f_swe = build_feature_value(
        AVALANCHE_FEATURE_SPECS["swe_estimate_mm"],
        swe_val,
        snow_obs,
        cutoff_at,
        source_cadences,
    )
    f_temp = build_feature_value(
        AVALANCHE_FEATURE_SPECS["temp_mean_24h_c"],
        temp_mean,
        temp_obs,
        cutoff_at,
        source_cadences,
    )
    f_wind = build_feature_value(
        AVALANCHE_FEATURE_SPECS["wind_loading_kmh"],
        wind_max,
        wind_obs,
        cutoff_at,
        source_cadences,
    )
    f_slope = build_feature_value(
        AVALANCHE_FEATURE_SPECS["slope_deg"],
        terrain.slope_deg if terrain else None,
        [],
        cutoff_at,
    )
    f_aspect = build_feature_value(
        AVALANCHE_FEATURE_SPECS["aspect_deg"],
        terrain.aspect_deg if terrain else None,
        [],
        cutoff_at,
    )
    f_elevation = build_feature_value(
        AVALANCHE_FEATURE_SPECS["elevation_m"],
        terrain.elevation_m if terrain else None,
        [],
        cutoff_at,
    )

    all_features = [
        f_new_snow,
        f_snow_depth,
        f_swe,
        f_temp,
        f_wind,
        f_slope,
        f_aspect,
        f_elevation,
    ]
    return AvalancheFeatureVector(
        location_id=location_id,
        cutoff_at=cutoff_at,
        new_snow_24h_cm=f_new_snow,
        snow_depth_cm=f_snow_depth,
        swe_estimate_mm=f_swe,
        temp_mean_24h_c=f_temp,
        wind_loading_kmh=f_wind,
        slope_deg=f_slope,
        aspect_deg=f_aspect,
        elevation_m=f_elevation,
        missing_count=sum(1 for f in all_features if f.is_missing),
        overall_freshness=aggregate_overall_freshness(all_features),
    )
