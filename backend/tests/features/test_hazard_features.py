"""Unit tests for separate flood and avalanche feature engineering pipelines."""

from datetime import UTC, datetime, timedelta

import pytest

from app.features.avalanche import extract_avalanche_features
from app.features.flood import extract_flood_features
from app.features.metadata import (
    AVALANCHE_FEATURE_SPECS,
    FLOOD_FEATURE_SPECS,
    TerrainContext,
)
from app.schemas.common import FreshnessStatus, HazardType
from app.schemas.observation import ALLOWED_UNITS, ObservationContract, ObservationMetric

CUTOFF = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)


def _obs(
    obs_id: str,
    metric: ObservationMetric,
    value: float,
    hours_before_cutoff: float,
    *,
    location_id: str = "JK-SGR-01",
    source_id: str = "imd-demo",
) -> ObservationContract:
    return ObservationContract(
        observation_id=obs_id,
        location_id=location_id,
        source_id=source_id,
        observed_at=CUTOFF - timedelta(hours=hours_before_cutoff),
        metric=metric,
        value=value,
        unit=ALLOWED_UNITS[metric],
    )


def test_hazard_feature_specs_remain_separate() -> None:
    flood_names = set(FLOOD_FEATURE_SPECS.keys())
    avalanche_names = set(AVALANCHE_FEATURE_SPECS.keys())
    assert flood_names.isdisjoint(avalanche_names)
    assert all(s.hazard_type == HazardType.FLOOD for s in FLOOD_FEATURE_SPECS.values())
    assert all(
        s.hazard_type == HazardType.AVALANCHE for s in AVALANCHE_FEATURE_SPECS.values()
    )


def test_flood_temporal_windows_and_no_future_leakage() -> None:
    observations = [
        _obs("r1", ObservationMetric.RAIN_MM, 10.0, 0.5, source_id="imd-aws"),
        _obs("r2", ObservationMetric.RAIN_MM, 15.0, 10.0, source_id="imd-aws"),
        _obs("r3", ObservationMetric.RAIN_MM, 20.0, 48.0, source_id="imd-aws"),
        _obs("r4", ObservationMetric.RAIN_MM, 999.0, -0.1, source_id="imd-aws"),  # future!
        _obs("r5", ObservationMetric.RAIN_MM, 50.0, 80.0, source_id="imd-aws"),  # >72h
        _obs("l1", ObservationMetric.RIVER_LEVEL_M, 2.0, 4.0, source_id="cwc-gauge"),
        _obs("l2", ObservationMetric.RIVER_LEVEL_M, 3.0, 0.5, source_id="cwc-gauge"),
        _obs("l3", ObservationMetric.RIVER_LEVEL_M, 9.9, -1.0, source_id="cwc-gauge"),  # future!
        _obs("other", ObservationMetric.RAIN_MM, 100.0, 0.5, location_id="UK-JSH-01"),
        _obs("snow", ObservationMetric.SNOW_DEPTH_CM, 80.0, 0.5),  # avalanche metric ignored
    ]
    terrain = TerrainContext(drainage_density=1.85)
    vec = extract_flood_features("JK-SGR-01", observations, CUTOFF, terrain=terrain)

    assert vec.hazard_type == HazardType.FLOOD
    assert vec.rain_1h_mm.value == pytest.approx(10.0)
    assert vec.rain_24h_mm.value == pytest.approx(25.0)
    assert vec.antecedent_rain_72h_mm.value == pytest.approx(20.0)
    assert vec.river_level_m.value == pytest.approx(3.0)
    assert vec.river_level_rate_m_per_h.value == pytest.approx(1.0 / 3.5, rel=1e-3)
    assert vec.drainage_density.value == pytest.approx(1.85)
    assert vec.missing_count == 0
    assert vec.overall_freshness == FreshnessStatus.FRESH
    assert vec.rain_1h_mm.source_ids == ["imd-aws"]
    assert vec.river_level_m.source_ids == ["cwc-gauge"]


def test_avalanche_features_and_no_future_leakage() -> None:
    observations = [
        _obs("s1", ObservationMetric.SNOW_DEPTH_CM, 70.0, 20.0, location_id="LA-DRS-01"),
        _obs("s2", ObservationMetric.SNOW_DEPTH_CM, 92.0, 1.0, location_id="LA-DRS-01"),
        _obs(
            "s_fut", ObservationMetric.SNOW_DEPTH_CM, 200.0, -0.5, location_id="LA-DRS-01"
        ),
        _obs("t1", ObservationMetric.TEMP_C, -8.0, 12.0, location_id="LA-DRS-01"),
        _obs("t2", ObservationMetric.TEMP_C, -4.0, 1.0, location_id="LA-DRS-01"),
        _obs("w1", ObservationMetric.WIND_KMH, 35.0, 6.0, location_id="LA-DRS-01"),
        _obs("w2", ObservationMetric.WIND_KMH, 55.0, 1.0, location_id="LA-DRS-01"),
        _obs("rain", ObservationMetric.RAIN_MM, 40.0, 1.0, location_id="LA-DRS-01"),  # ignored
    ]
    terrain = TerrainContext(elevation_m=3280.0, slope_deg=34.5, aspect_deg=45.0)
    vec = extract_avalanche_features(
        "LA-DRS-01", observations, CUTOFF, terrain=terrain
    )

    assert vec.hazard_type == HazardType.AVALANCHE
    assert vec.new_snow_24h_cm.value == pytest.approx(22.0)
    assert vec.snow_depth_cm.value == pytest.approx(92.0)
    assert vec.swe_estimate_mm.value == pytest.approx(230.0)
    assert vec.temp_mean_24h_c.value == pytest.approx(-6.0)
    assert vec.wind_loading_kmh.value == pytest.approx(55.0)
    assert vec.slope_deg.value == pytest.approx(34.5)
    assert vec.aspect_deg.value == pytest.approx(45.0)
    assert vec.elevation_m.value == pytest.approx(3280.0)
    assert vec.missing_count == 0
    assert vec.overall_freshness == FreshnessStatus.FRESH


def test_missing_values_and_stale_freshness_edge_cases() -> None:
    stale_obs = [
        _obs("s1", ObservationMetric.SNOW_DEPTH_CM, 50.0, 5.0, location_id="LA-DRS-01"),
    ]
    # Cadence = 60 min -> 5h (300 min) > 90 min -> STALE; single obs -> new_snow missing
    aval = extract_avalanche_features(
        "LA-DRS-01",
        stale_obs,
        CUTOFF,
        source_cadences={"imd-demo": 60},
    )
    assert aval.snow_depth_cm.value == pytest.approx(50.0)
    assert aval.snow_depth_cm.freshness == FreshnessStatus.STALE
    assert aval.new_snow_24h_cm.is_missing is True
    assert aval.new_snow_24h_cm.value is None
    assert aval.temp_mean_24h_c.is_missing is True
    assert aval.slope_deg.is_missing is True
    assert aval.overall_freshness == FreshnessStatus.STALE
    assert aval.missing_count == 6

    empty_flood = extract_flood_features("JK-SGR-01", [], CUTOFF)
    assert empty_flood.missing_count == 6
    assert empty_flood.overall_freshness == FreshnessStatus.UNKNOWN


def test_naive_cutoff_rejected() -> None:
    naive = datetime(2026, 11, 26, 12, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        extract_flood_features("JK-SGR-01", [], naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        extract_avalanche_features("LA-DRS-01", [], naive)
