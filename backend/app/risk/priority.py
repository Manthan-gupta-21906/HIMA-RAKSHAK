"""Priority calculation and emergency response ranking combining hazard and impact."""

from app.risk.impact import compute_impact_score
from app.schemas.common import RiskClass
from app.schemas.exposure import LocationExposureProfile, PriorityAssessment
from app.schemas.risk import RiskAssessmentContract

# Hazard class multiplier mapping (when numerical score is None, e.g. indicative)
HAZARD_CLASS_DEFAULT_WEIGHT: dict[RiskClass, float] = {
    RiskClass.UNSUPPORTED: 0.0,
    RiskClass.LOW: 0.15,
    RiskClass.MODERATE: 0.45,
    RiskClass.HIGH: 0.75,
    RiskClass.SEVERE: 0.95,
}

DEFAULT_PRIORITY_WEIGHTS: dict[str, float] = {
    "hazard_weight": 0.50,
    "impact_weight": 0.50,
}


def classify_priority_level(score: float, risk_class: RiskClass) -> str:
    """Categorize priority score into decision action tiers."""
    if risk_class == RiskClass.UNSUPPORTED:
        return "LOW"
    if score >= 0.70 or risk_class == RiskClass.SEVERE:
        return "CRITICAL"
    if score >= 0.45:
        return "HIGH"
    if score >= 0.25:
        return "MEDIUM"
    return "LOW"


def calculate_priority_assessment(
    hazard_assessment: RiskAssessmentContract,
    exposure_profile: LocationExposureProfile,
    weights: dict[str, float] | None = None,
) -> PriorityAssessment:
    """Calculate priority assessment without modifying the underlying hazard assessment.

    Formula:
      effective_hazard = hazard_assessment.score if present else class_default
      priority_score = (hazard_weight * effective_hazard) + (impact_weight * impact_score)
    """
    w = weights or DEFAULT_PRIORITY_WEIGHTS
    impact_score, breakdown = compute_impact_score(exposure_profile)

    if hazard_assessment.score is not None:
        h_score = hazard_assessment.score
    else:
        h_score = HAZARD_CLASS_DEFAULT_WEIGHT.get(hazard_assessment.risk_class, 0.0)

    # Calculate overall priority score
    h_w = w["hazard_weight"]
    i_w = w["impact_weight"]

    priority_score = (h_w * h_score) + (i_w * impact_score)
    priority_score = round(min(1.0, max(0.0, priority_score)), 4)

    # Preserve unchanged original hazard score
    orig_hazard_score = hazard_assessment.score

    breakdown["hazard_effective"] = round(h_score, 4)
    breakdown["impact_total"] = impact_score

    priority_level = classify_priority_level(priority_score, hazard_assessment.risk_class)

    return PriorityAssessment(
        location_id=hazard_assessment.location_id,
        evaluated_at=hazard_assessment.assessed_at,
        hazard_score=orig_hazard_score,
        hazard_risk_class=hazard_assessment.risk_class,
        exposure_score=impact_score,
        impact_score=impact_score,
        priority_score=priority_score,
        coverage_status=exposure_profile.coverage_status,
        priority_level=priority_level,
        weights_used=w,
        breakdown=breakdown,
    )
