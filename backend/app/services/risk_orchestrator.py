"""Multi-hazard risk orchestrator coordinating distinct hazard pipelines into a shared state."""

from datetime import UTC, datetime

from app.avalanche.readiness import evaluate_avalanche_readiness
from app.features.avalanche import AvalancheFeatureVector
from app.features.flood import FloodFeatureVector
from app.flood.model import FloodBaselineClassifier
from app.flood.predict import predict_flood_risk
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.risk import LocationRiskState, RiskAssessmentContract

RISK_CLASS_SEVERITY_ORDER: dict[RiskClass, int] = {
    RiskClass.UNSUPPORTED: 0,
    RiskClass.LOW: 1,
    RiskClass.MODERATE: 2,
    RiskClass.HIGH: 3,
    RiskClass.SEVERE: 4,
}


class RiskOrchestrator:
    """Orchestrates separate hazard assessment pathways into a unified spatial state.

    Crucially, hazard pathways remain independent:
    - Flood evaluation uses flood telemetry, rainfall, and baseline model.
    - Avalanche evaluation uses snowpack, terrain, and readiness gating.
    - The outputs are compiled into LocationRiskState without blending underlying risk scores.
    """

    def __init__(self, repository: RiskAssessmentRepository) -> None:
        self.repository = repository

    def assess_flood(
        self,
        features: FloodFeatureVector,
        model: FloodBaselineClassifier | None = None,
        source_meta: ProvenanceMeta | None = None,
        lead_time_hours: int = 24,
    ) -> RiskAssessmentContract:
        """Run flood hazard pathway assessment."""
        assessed_at = features.cutoff_at
        risk_id = f"risk-flood-{features.location_id}-{int(assessed_at.timestamp())}"

        meta = source_meta or ProvenanceMeta(
            source_id="cwc-flood-telemetry",
            source_name="Central Water Commission Telemetry",
            licence="Open Government Data Licence India",
            is_demo_fixture=True,
            ingested_at=datetime.now(UTC),
        )

        if model is None:
            # Model unavailable or uncalibrated; output unsupported state
            contract = RiskAssessmentContract(
                risk_id=risk_id,
                location_id=features.location_id,
                hazard_type=HazardType.FLOOD,
                risk_class=RiskClass.UNSUPPORTED,
                score=None,
                confidence=0.0,
                lead_time_hours=lead_time_hours,
                freshness=features.overall_freshness,
                prediction_status=PredictionStatus.UNSUPPORTED,
                readiness_reason="Baseline model is not fitted or calibrated with verified labels.",
                assessed_at=assessed_at,
                model_version=None,
                provenance=meta,
            )
            return self.repository.save(contract)

        # Predict using baseline classifier
        pred = predict_flood_risk(model, features, sample_id=risk_id)

        # Map freshness to prediction status
        status = (
            PredictionStatus.READY
            if features.overall_freshness == FreshnessStatus.FRESH
            else PredictionStatus.STALE
        )

        contract = RiskAssessmentContract(
            risk_id=risk_id,
            location_id=features.location_id,
            hazard_type=HazardType.FLOOD,
            risk_class=pred.risk_class,
            score=pred.flood_probability,
            confidence=0.85 if status == PredictionStatus.READY else 0.50,
            lead_time_hours=lead_time_hours,
            freshness=features.overall_freshness,
            prediction_status=status,
            readiness_reason="; ".join(pred.limitations) if pred.limitations else None,
            assessed_at=assessed_at,
            model_version=pred.model_version,
            provenance=meta,
        )
        return self.repository.save(contract)

    def assess_avalanche(
        self,
        features: AvalancheFeatureVector,
        historical_event_labels_count: int = 0,
        historical_non_event_labels_count: int = 0,
        source_meta: ProvenanceMeta | None = None,
        lead_time_hours: int = 12,
    ) -> RiskAssessmentContract:
        """Run avalanche hazard pathway assessment using scientific readiness gating."""
        assessed_at = features.cutoff_at
        risk_id = f"risk-avalanche-{features.location_id}-{int(assessed_at.timestamp())}"

        meta = source_meta or ProvenanceMeta(
            source_id="dgre-snow-telemetry",
            source_name="Defence Geoinformatics Research Establishment",
            licence="Official Research Pilot Licence",
            is_demo_fixture=True,
            ingested_at=datetime.now(UTC),
        )

        readiness = evaluate_avalanche_readiness(
            features=features,
            historical_event_labels_count=historical_event_labels_count,
            historical_non_event_labels_count=historical_non_event_labels_count,
            evaluation_time=assessed_at,
        )

        if not readiness.is_validated_forecast_allowed:
            # Unsupported or indicative-screening state
            pred_status = (
                PredictionStatus.UNSUPPORTED
                if readiness.status == "unsupported"
                else PredictionStatus.INDICATIVE
            )
            risk_cls = (
                RiskClass.UNSUPPORTED
                if pred_status == PredictionStatus.UNSUPPORTED
                else RiskClass.MODERATE
            )
            # Scores are strictly None for unsupported states to avoid false precision
            score = None if pred_status == PredictionStatus.UNSUPPORTED else 0.50

            contract = RiskAssessmentContract(
                risk_id=risk_id,
                location_id=features.location_id,
                hazard_type=HazardType.AVALANCHE,
                risk_class=risk_cls,
                score=score,
                confidence=0.30 if pred_status == PredictionStatus.INDICATIVE else 0.0,
                lead_time_hours=lead_time_hours,
                freshness=features.overall_freshness,
                prediction_status=pred_status,
                readiness_reason="; ".join(readiness.reasons),
                assessed_at=assessed_at,
                model_version="readiness-gated-v1",
                provenance=meta,
            )
            return self.repository.save(contract)

        # Full supported state
        contract = RiskAssessmentContract(
            risk_id=risk_id,
            location_id=features.location_id,
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.HIGH,
            score=0.75,
            confidence=0.90,
            lead_time_hours=lead_time_hours,
            freshness=features.overall_freshness,
            prediction_status=PredictionStatus.READY,
            readiness_reason=None,
            assessed_at=assessed_at,
            model_version="avalanche-validated-v1",
            provenance=meta,
        )
        return self.repository.save(contract)

    def get_location_risk_state(self, location_id: str) -> LocationRiskState:
        """Compose co-located hazard states into a shared spatial state without blending scores."""
        flood_latest = self.repository.get_latest_for_location_and_hazard(
            location_id, HazardType.FLOOD
        )
        avalanche_latest = self.repository.get_latest_for_location_and_hazard(
            location_id, HazardType.AVALANCHE
        )

        now = datetime.now(UTC)
        updated_at = now
        candidates = [c for c in [flood_latest, avalanche_latest] if c is not None]
        if candidates:
            updated_at = max(c.assessed_at for c in candidates)

        # Determine highest risk class and primary hazard
        highest_class = RiskClass.LOW
        primary_hazard = None
        max_severity = -1

        for assessment in candidates:
            sev = RISK_CLASS_SEVERITY_ORDER.get(assessment.risk_class, 0)
            if sev > max_severity:
                max_severity = sev
                highest_class = assessment.risk_class
                primary_hazard = assessment.hazard_type

        return LocationRiskState(
            location_id=location_id,
            updated_at=updated_at,
            flood=flood_latest,
            avalanche=avalanche_latest,
            primary_hazard=primary_hazard,
            highest_risk_class=highest_class,
        )
