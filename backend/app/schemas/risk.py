"""Risk assessment contracts including uncertainty, freshness, and readiness."""

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import (
    AwareDatetime,
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)


class RiskAssessmentContract(BaseModel):
    """Shared spatial risk assessment produced by a hazard pathway."""

    risk_id: str = Field(..., min_length=2, max_length=64)
    location_id: str = Field(..., min_length=3, max_length=32)
    hazard_type: HazardType
    risk_class: RiskClass
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    lead_time_hours: int = Field(..., ge=0, le=168)
    freshness: FreshnessStatus
    prediction_status: PredictionStatus
    readiness_reason: str | None = Field(default=None, max_length=300)
    assessed_at: AwareDatetime
    provenance: ProvenanceMeta

    @model_validator(mode="after")
    def validate_unsupported_state(self) -> "RiskAssessmentContract":
        if self.prediction_status == PredictionStatus.UNSUPPORTED:
            if self.risk_class != RiskClass.UNSUPPORTED:
                raise ValueError(
                    "risk_class must be 'unsupported' when prediction_status is 'unsupported'."
                )
            if self.score is not None:
                raise ValueError("score must be None when prediction_status is 'unsupported'.")
        return self
