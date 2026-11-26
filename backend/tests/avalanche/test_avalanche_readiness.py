"""Tests for avalanche readiness rules, status states, and evidentiary gating."""

from datetime import UTC, datetime

from app.avalanche.readiness import evaluate_avalanche_readiness
from app.avalanche.requirements import (
    REASON_MISSING_EVENT_LABELS,
    REASON_MISSING_SNOWPACK,
    REASON_STALE_SNOWPACK,
    REASON_TERRAIN_ONLY,
    AvalancheRequirements,
)
from app.avalanche.status import AvalancheOperationalStatus
from app.features.avalanche import AvalancheFeatureVector
from app.features.metadata import FeatureValue
from app.schemas.common import FreshnessStatus, HazardType


def _make_avalanche_vector(
    location_id: str = "loc-solang-01",
    cutoff_at: datetime | None = None,
    new_snow_val: float | None = 15.0,
    snow_depth_val: float | None = 85.0,
    snow_freshness: FreshnessStatus = FreshnessStatus.FRESH,
    temp_val: float | None = -4.5,
    temp_freshness: FreshnessStatus = FreshnessStatus.FRESH,
    wind_val: float | None = 35.0,
    wind_freshness: FreshnessStatus = FreshnessStatus.FRESH,
    slope_val: float | None = 34.0,
    aspect_val: float | None = 45.0,
    elevation_val: float | None = 3200.0,
) -> AvalancheFeatureVector:
    ts = cutoff_at or datetime.now(UTC)

    f_new_snow = FeatureValue(
        name="new_snow_24h_cm",
        value=new_snow_val,
        unit="cm",
        is_missing=new_snow_val is None,
        freshness=snow_freshness,
    )
    f_snow_depth = FeatureValue(
        name="snow_depth_cm",
        value=snow_depth_val,
        unit="cm",
        is_missing=snow_depth_val is None,
        freshness=snow_freshness,
    )
    f_swe = FeatureValue(
        name="swe_estimate_mm",
        value=snow_depth_val * 2.5 if snow_depth_val is not None else None,
        unit="mm",
        is_missing=snow_depth_val is None,
        freshness=snow_freshness,
    )
    f_temp = FeatureValue(
        name="temp_mean_24h_c",
        value=temp_val,
        unit="c",
        is_missing=temp_val is None,
        freshness=temp_freshness,
    )
    f_wind = FeatureValue(
        name="wind_loading_kmh",
        value=wind_val,
        unit="km/h",
        is_missing=wind_val is None,
        freshness=wind_freshness,
    )
    f_slope = FeatureValue(
        name="slope_deg",
        value=slope_val,
        unit="deg",
        is_missing=slope_val is None,
    )
    f_aspect = FeatureValue(
        name="aspect_deg",
        value=aspect_val,
        unit="deg",
        is_missing=aspect_val is None,
    )
    f_elevation = FeatureValue(
        name="elevation_m",
        value=elevation_val,
        unit="m",
        is_missing=elevation_val is None,
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
        hazard_type=HazardType.AVALANCHE,
        location_id=location_id,
        cutoff_at=ts,
        new_snow_24h_cm=f_new_snow,
        snow_depth_cm=f_snow_depth,
        swe_estimate_mm=f_swe,
        temp_mean_24h_c=f_temp,
        wind_loading_kmh=f_wind,
        slope_deg=f_slope,
        aspect_deg=f_aspect,
        elevation_m=f_elevation,
        missing_count=sum(1 for f in all_features if f.is_missing),
        overall_freshness=snow_freshness,
    )


def test_terrain_only_inputs_cannot_produce_validated_forecast():
    """Verify terrain-only inputs strictly result in UNSUPPORTED and disallow forecasting."""
    vector = _make_avalanche_vector(
        new_snow_val=None,
        snow_depth_val=None,
        temp_val=None,
        wind_val=None,
        slope_val=38.0,
        aspect_val=180.0,
        elevation_val=3100.0,
    )

    assessment = evaluate_avalanche_readiness(
        features=vector,
        historical_event_labels_count=15,
        historical_non_event_labels_count=15,
    )

    assert assessment.status == AvalancheOperationalStatus.UNSUPPORTED
    assert assessment.is_validated_forecast_allowed is False
    assert REASON_TERRAIN_ONLY in assessment.reasons
    assert "snowpack_telemetry" in assessment.missing_requirements


def test_missing_snowpack_blocks_validated_status():
    """Verify missing snowpack telemetry prevents supported status."""
    vector = _make_avalanche_vector(
        new_snow_val=None,
        snow_depth_val=None,
        temp_val=-5.0,
        wind_val=25.0,
    )

    assessment = evaluate_avalanche_readiness(
        features=vector,
        historical_event_labels_count=15,
        historical_non_event_labels_count=15,
    )

    assert assessment.status == AvalancheOperationalStatus.UNSUPPORTED
    assert assessment.is_validated_forecast_allowed is False
    assert REASON_MISSING_SNOWPACK in assessment.reasons
    assert "snowpack_telemetry" in assessment.missing_requirements


def test_stale_snowpack_blocks_validated_status():
    """Verify stale snowpack observations prevent supported status."""
    vector = _make_avalanche_vector(
        snow_freshness=FreshnessStatus.STALE,
    )

    assessment = evaluate_avalanche_readiness(
        features=vector,
        historical_event_labels_count=15,
        historical_non_event_labels_count=15,
    )

    assert assessment.status == AvalancheOperationalStatus.UNSUPPORTED
    assert assessment.is_validated_forecast_allowed is False
    assert REASON_STALE_SNOWPACK in assessment.reasons
    assert "fresh_snowpack_telemetry" in assessment.missing_requirements


def test_missing_event_labels_prevents_supervised_validation_claims():
    """Verify fresh telemetry with missing labels yields indicative-screening, not supported."""
    vector = _make_avalanche_vector(
        snow_freshness=FreshnessStatus.FRESH,
        temp_freshness=FreshnessStatus.FRESH,
        wind_freshness=FreshnessStatus.FRESH,
    )

    # 0 verified event labels
    assessment = evaluate_avalanche_readiness(
        features=vector,
        historical_event_labels_count=0,
        historical_non_event_labels_count=0,
    )

    assert assessment.status == AvalancheOperationalStatus.INDICATIVE_SCREENING
    assert assessment.is_validated_forecast_allowed is False
    assert REASON_MISSING_EVENT_LABELS in assessment.reasons
    assert "verified_historical_event_labels" in assessment.missing_requirements


def test_fully_supported_status_when_all_evidence_present():
    """Verify SUPPORTED status when snowpack, weather, terrain, and labels are certified."""
    vector = _make_avalanche_vector(
        snow_freshness=FreshnessStatus.FRESH,
        temp_freshness=FreshnessStatus.FRESH,
        wind_freshness=FreshnessStatus.FRESH,
    )

    assessment = evaluate_avalanche_readiness(
        features=vector,
        historical_event_labels_count=12,
        historical_non_event_labels_count=12,
        requirements=AvalancheRequirements(
            min_historical_event_labels=10,
            min_historical_non_event_labels=10,
        ),
    )

    assert assessment.status == AvalancheOperationalStatus.SUPPORTED
    assert assessment.is_validated_forecast_allowed is True
    assert len(assessment.reasons) == 0
    assert len(assessment.missing_requirements) == 0


def test_custom_requirements_thresholds():
    """Verify that customized threshold requirements properly enforce readiness gating."""
    custom_req = AvalancheRequirements(
        min_historical_event_labels=25,
        min_historical_non_event_labels=25,
    )

    vector = _make_avalanche_vector()

    assessment = evaluate_avalanche_readiness(
        features=vector,
        historical_event_labels_count=15,
        historical_non_event_labels_count=15,
        requirements=custom_req,
    )

    assert assessment.status == AvalancheOperationalStatus.INDICATIVE_SCREENING
    assert assessment.is_validated_forecast_allowed is False
    assert REASON_MISSING_EVENT_LABELS in assessment.reasons
