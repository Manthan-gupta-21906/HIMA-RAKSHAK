"""Inference service for flood prediction with versioning, confidence, and explicit limitations."""

from pydantic import BaseModel, Field

from app.features.flood import FloodFeatureVector
from app.flood.dataset import FloodSample, extract_feature_array
from app.flood.model import FloodBaselineClassifier
from app.schemas.common import AwareDatetime, RiskClass


class FloodPredictionOutput(BaseModel):
    """Standard prediction response carrying model provenance, limitations, and risk class."""

    location_id: str
    prediction_time: AwareDatetime
    flood_probability: float = Field(ge=0.0, le=1.0)
    risk_class: RiskClass
    predicted_class: int
    model_version: str
    limitations: list[str]
    missing_features_count: int


def classify_risk_class(prob: float) -> RiskClass:
    """Map probability to standardized multi-tiered risk class."""
    if prob >= 0.8:
        return RiskClass.SEVERE
    if prob >= 0.6:
        return RiskClass.HIGH
    if prob >= 0.35:
        return RiskClass.MODERATE
    return RiskClass.LOW


def predict_flood_risk(
    model: FloodBaselineClassifier,
    features: FloodFeatureVector,
    sample_id: str = "infer-1",
) -> FloodPredictionOutput:
    """Generate risk assessment for a feature vector using the baseline classifier."""
    sample = FloodSample(
        sample_id=sample_id,
        location_id=features.location_id,
        timestamp=features.cutoff_at,
        features=features,
    )

    x = extract_feature_array(sample)
    proba = model.predict_proba([x])[0]
    predicted_class = 1 if proba >= model.decision_threshold else 0

    return FloodPredictionOutput(
        location_id=features.location_id,
        prediction_time=features.cutoff_at,
        flood_probability=round(proba, 4),
        risk_class=classify_risk_class(proba),
        predicted_class=predicted_class,
        model_version=model.metadata.model_version,
        limitations=model.metadata.limitations,
        missing_features_count=features.missing_count,
    )
