"""Repository for persisting, retrieving, and querying multi-hazard risk assessments."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.risk_assessment import RiskAssessmentModel
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.risk import RiskAssessmentContract


class RiskAssessmentRepository:
    """Manages transactional persistence and retrieval of hazard risk assessments."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure datetimes returned from database driver carry UTC timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    def to_contract(self, model: RiskAssessmentModel) -> RiskAssessmentContract:
        """Convert an ORM model instance into a validated RiskAssessmentContract."""
        return RiskAssessmentContract(
            risk_id=model.risk_id,
            location_id=model.location_id,
            hazard_type=HazardType(model.hazard_type),
            risk_class=RiskClass(model.risk_class),
            score=model.score,
            confidence=model.confidence,
            lead_time_hours=model.lead_time_hours,
            freshness=FreshnessStatus(model.freshness),
            prediction_status=PredictionStatus(model.prediction_status),
            readiness_reason=model.readiness_reason,
            assessed_at=self._ensure_utc(model.assessed_at),
            model_version=model.model_version,
            provenance=ProvenanceMeta(
                source_id=model.source_id,
                source_name=model.source_name,
                licence=model.licence,
                is_demo_fixture=model.is_demo_fixture,
                ingested_at=self._ensure_utc(model.ingested_at),
            ),
        )

    def save(self, contract: RiskAssessmentContract) -> RiskAssessmentContract:
        """Persist or update an assessment record idempotently based on natural key."""
        stmt = select(RiskAssessmentModel).where(
            RiskAssessmentModel.location_id == contract.location_id,
            RiskAssessmentModel.hazard_type == contract.hazard_type.value,
            RiskAssessmentModel.assessed_at == contract.assessed_at,
        )
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing:
            existing.risk_class = contract.risk_class.value
            existing.score = contract.score
            existing.confidence = contract.confidence
            existing.lead_time_hours = contract.lead_time_hours
            existing.freshness = contract.freshness.value
            existing.prediction_status = contract.prediction_status.value
            existing.readiness_reason = contract.readiness_reason
            existing.model_version = contract.model_version
            existing.source_id = contract.provenance.source_id
            existing.source_name = contract.provenance.source_name
            existing.licence = contract.provenance.licence
            existing.is_demo_fixture = contract.provenance.is_demo_fixture
            existing.ingested_at = contract.provenance.ingested_at
            self.session.flush()
            return self.to_contract(existing)

        model = RiskAssessmentModel(
            risk_id=contract.risk_id,
            location_id=contract.location_id,
            hazard_type=contract.hazard_type.value,
            risk_class=contract.risk_class.value,
            score=contract.score,
            confidence=contract.confidence,
            lead_time_hours=contract.lead_time_hours,
            freshness=contract.freshness.value,
            prediction_status=contract.prediction_status.value,
            readiness_reason=contract.readiness_reason,
            assessed_at=contract.assessed_at,
            model_version=contract.model_version,
            source_id=contract.provenance.source_id,
            source_name=contract.provenance.source_name,
            licence=contract.provenance.licence,
            is_demo_fixture=contract.provenance.is_demo_fixture,
            ingested_at=contract.provenance.ingested_at,
        )
        self.session.add(model)
        self.session.flush()
        return self.to_contract(model)

    def save_many(
        self, contracts: Sequence[RiskAssessmentContract]
    ) -> list[RiskAssessmentContract]:
        """Save a batch of risk assessment contracts in a single transaction."""
        return [self.save(c) for c in contracts]

    def get_by_id(self, risk_id: str) -> RiskAssessmentContract | None:
        """Lookup assessment by unique risk ID."""
        model = self.session.get(RiskAssessmentModel, risk_id)
        return self.to_contract(model) if model else None

    def get_latest_for_location_and_hazard(
        self, location_id: str, hazard_type: HazardType
    ) -> RiskAssessmentContract | None:
        """Fetch the most recent assessment for a specific location and hazard pathway."""
        stmt = (
            select(RiskAssessmentModel)
            .where(
                RiskAssessmentModel.location_id == location_id,
                RiskAssessmentModel.hazard_type == hazard_type.value,
            )
            .order_by(desc(RiskAssessmentModel.assessed_at))
            .limit(1)
        )
        model = self.session.execute(stmt).scalar_one_or_none()
        return self.to_contract(model) if model else None

    def list_history(
        self,
        location_id: str,
        hazard_type: HazardType | None = None,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[RiskAssessmentContract]:
        """List historical assessments for a location with optional hazard and time filtering."""
        stmt = select(RiskAssessmentModel).where(RiskAssessmentModel.location_id == location_id)
        if hazard_type:
            stmt = stmt.where(RiskAssessmentModel.hazard_type == hazard_type.value)
        if since:
            stmt = stmt.where(RiskAssessmentModel.assessed_at >= since)
        stmt = stmt.order_by(desc(RiskAssessmentModel.assessed_at)).limit(limit)

        records = self.session.execute(stmt).scalars().all()
        return [self.to_contract(r) for r in records]
