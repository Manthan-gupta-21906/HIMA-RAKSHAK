"""Flood hazard feature extraction pipeline."""

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.features.common import (
    aggregate_overall_freshness,
    build_feature_value,
    compute_rate_of_change,
    filter_observations_in_window,
)
from app.features.metadata import FLOOD_FEATURE_SPECS, FeatureValue, TerrainContext
from app.schemas.common import AwareDatetime, FreshnessStatus, HazardType
from app.schemas.observation import ObservationContract, ObservationMetric


class FloodFeatureVector(BaseModel):
    """Independent feature vector for the flood risk pathway."""

    hazard_type: Literal[HazardType.FLOOD] = HazardType.FLOOD
    location_id: str
    cutoff_at: AwareDatetime
    rain_1h_mm: FeatureValue
    rain_24h_mm: FeatureValue
    antecedent_rain_72h_mm: FeatureValue
    river_level_m: FeatureValue
    river_level_rate_m_per_h: FeatureValue
    drainage_density: FeatureValue
    missing_count: int
    overall_freshness: FreshnessStatus


def extract_flood_features(
    location_id: str,
    observations: Sequence[ObservationContract],
    cutoff_at: datetime,
    terrain: TerrainContext | None = None,
    source_cadences: dict[str, int] | None = None,
) -> FloodFeatureVector:
    """Compute flood features strictly up to ``cutoff_at`` without future leakage."""
    rain_1h_obs = filter_observations_in_window(
        observations, location_id, cutoff_at, metric=ObservationMetric.RAIN_MM, window_hours=1
    )
    rain_24h_obs = filter_observations_in_window(
        observations, location_id, cutoff_at, metric=ObservationMetric.RAIN_MM, window_hours=24
    )
    ant_72h_obs = filter_observations_in_window(
        observations,
        location_id,
        cutoff_at,
        metric=ObservationMetric.RAIN_MM,
        window_hours=72,
        end_offset_hours=24,
    )
    river_24h_obs = filter_observations_in_window(
        observations,
        location_id,
        cutoff_at,
        metric=ObservationMetric.RIVER_LEVEL_M,
        window_hours=24,
    )
    river_6h_obs = filter_observations_in_window(
        observations,
        location_id,
        cutoff_at,
        metric=ObservationMetric.RIVER_LEVEL_M,
        window_hours=6,
    )

    f_rain_1h = build_feature_value(
        FLOOD_FEATURE_SPECS["rain_1h_mm"],
        sum(o.value for o in rain_1h_obs) if rain_1h_obs else None,
        rain_1h_obs,
        cutoff_at,
        source_cadences,
    )
    f_rain_24h = build_feature_value(
        FLOOD_FEATURE_SPECS["rain_24h_mm"],
        sum(o.value for o in rain_24h_obs) if rain_24h_obs else None,
        rain_24h_obs,
        cutoff_at,
        source_cadences,
    )
    f_ant_72h = build_feature_value(
        FLOOD_FEATURE_SPECS["antecedent_rain_72h_mm"],
        sum(o.value for o in ant_72h_obs) if ant_72h_obs else None,
        ant_72h_obs,
        cutoff_at,
        source_cadences,
    )
    f_river_lvl = build_feature_value(
        FLOOD_FEATURE_SPECS["river_level_m"],
        river_24h_obs[-1].value if river_24h_obs else None,
        river_24h_obs,
        cutoff_at,
        source_cadences,
    )
    f_river_rate = build_feature_value(
        FLOOD_FEATURE_SPECS["river_level_rate_m_per_h"],
        compute_rate_of_change(river_6h_obs),
        river_6h_obs,
        cutoff_at,
        source_cadences,
    )
    f_drainage = build_feature_value(
        FLOOD_FEATURE_SPECS["drainage_density"],
        terrain.drainage_density if terrain else None,
        [],
        cutoff_at,
        source_cadences,
    )

    current_features = [f_rain_1h, f_rain_24h, f_river_lvl, f_river_rate]
    all_features = [
        f_rain_1h,
        f_rain_24h,
        f_ant_72h,
        f_river_lvl,
        f_river_rate,
        f_drainage,
    ]
    return FloodFeatureVector(
        location_id=location_id,
        cutoff_at=cutoff_at,
        rain_1h_mm=f_rain_1h,
        rain_24h_mm=f_rain_24h,
        antecedent_rain_72h_mm=f_ant_72h,
        river_level_m=f_river_lvl,
        river_level_rate_m_per_h=f_river_rate,
        drainage_density=f_drainage,
        missing_count=sum(1 for f in all_features if f.is_missing),
        overall_freshness=aggregate_overall_freshness(current_features),
    )
