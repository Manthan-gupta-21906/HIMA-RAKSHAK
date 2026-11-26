"""Tests for spatial exposure aggregation, data coverage states, and asset counts."""

from datetime import UTC, datetime

from app.risk.exposure import build_exposure_profile
from app.risk.impact import compute_impact_score
from app.schemas.exposure import (
    ExposureAsset,
    ExposureCountType,
    ExposureCoverageStatus,
)


def _make_sample_assets() -> list[ExposureAsset]:
    return [
        ExposureAsset(
            asset_id="set-1",
            asset_type="settlement",
            name="Solang Village",
            count=1,
            count_type=ExposureCountType.VERIFIED,
            population_affected=1800,
        ),
        ExposureAsset(
            asset_id="home-block-1",
            asset_type="home",
            name="Solang Residential Cluster",
            count=320,
            count_type=ExposureCountType.ESTIMATED,
            population_affected=0,
        ),
        ExposureAsset(
            asset_id="road-nh3",
            asset_type="road",
            name="NH-3 Leh-Manali Highway",
            count=1,
            count_type=ExposureCountType.VERIFIED,
            metadata={"length_km": 14.5},
        ),
        ExposureAsset(
            asset_id="phc-1",
            asset_type="critical_facility",
            name="Primary Health Centre Solang",
            count=1,
            count_type=ExposureCountType.VERIFIED,
            is_critical=True,
        ),
    ]


def test_spatial_exposure_matches_fixtures():
    """Verify exposure aggregation computes correct population, homes, roads, and facilities."""
    assets = _make_sample_assets()
    now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    profile = build_exposure_profile(
        location_id="loc-solang-01",
        assets=assets,
        available_layers=["settlements", "homes", "roads", "critical_facilities"],
        evaluated_at=now,
    )

    assert profile.location_id == "loc-solang-01"
    assert profile.coverage_status == ExposureCoverageStatus.COMPLETE
    assert profile.population_exposed == 1800
    assert profile.settlements_count == 1
    assert profile.homes_exposed == 320
    assert profile.roads_exposed_km == 14.5
    assert profile.critical_facilities_count == 1
    assert len(profile.missing_layers) == 0


def test_missing_layers_produce_partial_coverage():
    """Verify that omitting required layers reports partial coverage and lists missing."""
    assets = [
        ExposureAsset(
            asset_id="set-1",
            asset_type="settlement",
            name="Village A",
            count=1,
            population_affected=500,
        )
    ]

    profile = build_exposure_profile(
        location_id="loc-partial-1",
        assets=assets,
        available_layers=["settlements"],
    )

    assert profile.coverage_status == ExposureCoverageStatus.PARTIAL
    assert "homes" in profile.missing_layers
    assert "roads" in profile.missing_layers
    assert "critical_facilities" in profile.missing_layers


def test_empty_layers_produce_unknown_coverage():
    """Verify empty layer inputs produce unknown coverage status."""
    profile = build_exposure_profile(
        location_id="loc-unknown-1",
        assets=[],
        available_layers=[],
    )

    assert profile.coverage_status == ExposureCoverageStatus.UNKNOWN
    assert len(profile.missing_layers) == 4


def test_impact_score_weights_are_deterministic():
    """Verify impact scoring is deterministic and bounded in [0.0, 1.0]."""
    assets = _make_sample_assets()
    layers = ["settlements", "homes", "roads", "critical_facilities"]
    profile = build_exposure_profile("loc-1", assets, available_layers=layers)

    score1, bd1 = compute_impact_score(profile)
    score2, bd2 = compute_impact_score(profile)

    assert score1 == score2
    assert bd1 == bd2
    assert 0.0 <= score1 <= 1.0
    assert "norm_population" in bd1
    assert "norm_critical_facilities" in bd1
