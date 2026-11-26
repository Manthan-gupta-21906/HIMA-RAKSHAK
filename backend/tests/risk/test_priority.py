"""Tests for priority index computation, hazard preservation, and scenario-based ranking."""

from datetime import UTC, datetime

from app.risk.exposure import build_exposure_profile
from app.risk.priority import calculate_priority_assessment
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.exposure import ExposureAsset
from app.schemas.risk import RiskAssessmentContract


def _make_hazard_contract(
    hazard_type: HazardType = HazardType.FLOOD,
    risk_class: RiskClass = RiskClass.HIGH,
    score: float | None = 0.70,
) -> RiskAssessmentContract:
    now = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    return RiskAssessmentContract(
        risk_id=f"risk-{hazard_type.value}-1",
        location_id="loc-test-1",
        hazard_type=hazard_type,
        risk_class=risk_class,
        score=score,
        confidence=0.85,
        lead_time_hours=24,
        freshness=FreshnessStatus.FRESH,
        prediction_status=PredictionStatus.READY
        if score is not None
        else PredictionStatus.UNSUPPORTED,
        assessed_at=now,
        provenance=ProvenanceMeta(
            source_id="src-1",
            source_name="Sensor",
            licence="MIT",
            is_demo_fixture=True,
            ingested_at=now,
        ),
    )


def test_hazard_score_remains_unchanged():
    """Verify priority assessment leaves original hazard score and risk class untouched."""
    contract = _make_hazard_contract(score=0.68)
    assets = [
        ExposureAsset(
            asset_id="set-1",
            asset_type="settlement",
            name="Town",
            population_affected=5000,
        )
    ]
    layers = ["settlements", "homes", "roads", "critical_facilities"]
    profile = build_exposure_profile("loc-test-1", assets, available_layers=layers)

    priority = calculate_priority_assessment(contract, profile)

    assert priority.hazard_score == 0.68
    assert priority.hazard_risk_class == RiskClass.HIGH
    assert priority.priority_score > 0.0


def test_priority_ranking_changes_under_controlled_scenarios():
    """Verify that higher exposure elevates priority ranking under equal hazard levels."""
    contract = _make_hazard_contract(score=0.50, risk_class=RiskClass.MODERATE)

    # Low exposure: small village, no critical facilities
    low_assets = [
        ExposureAsset(
            asset_id="set-small",
            asset_type="settlement",
            name="Hamlet",
            population_affected=100,
        )
    ]
    low_profile = build_exposure_profile("loc-1", low_assets)
    low_priority = calculate_priority_assessment(contract, low_profile)

    # High exposure: densely populated city, 5 hospitals, major highway
    high_assets = [
        ExposureAsset(
            asset_id="set-large",
            asset_type="settlement",
            name="District Capital",
            population_affected=9500,
        ),
        ExposureAsset(
            asset_id="phc-cluster",
            asset_type="critical_facility",
            name="Hospitals",
            count=6,
            is_critical=True,
        ),
        ExposureAsset(
            asset_id="nh-road",
            asset_type="road",
            name="Highway",
            metadata={"length_km": 40.0},
        ),
    ]
    high_profile = build_exposure_profile("loc-1", high_assets)
    high_priority = calculate_priority_assessment(contract, high_profile)

    # Priority score must be strictly higher for high exposure
    assert high_priority.priority_score > low_priority.priority_score
    assert high_priority.priority_level in ["HIGH", "CRITICAL"]
    assert low_priority.priority_level in ["LOW", "MEDIUM"]


def test_unsupported_hazard_priority_defaults_to_low():
    """Verify unsupported hazard state produces low priority without inventing false scores."""
    contract = _make_hazard_contract(
        hazard_type=HazardType.AVALANCHE,
        risk_class=RiskClass.UNSUPPORTED,
        score=None,
    )
    profile = build_exposure_profile("loc-1", [])

    priority = calculate_priority_assessment(contract, profile)
    assert priority.hazard_score is None
    assert priority.hazard_risk_class == RiskClass.UNSUPPORTED
    assert priority.priority_level == "LOW"
