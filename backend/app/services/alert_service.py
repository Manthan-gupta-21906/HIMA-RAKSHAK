"""Service layer for system-generated alerts, recommendations, and action history."""

from datetime import UTC, datetime
from uuid import uuid4

from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import AlertActionRecord, AlertStatus
from app.schemas.common import HazardType, PredictionStatus, RiskClass
from app.schemas.exposure import PriorityAssessment
from app.schemas.risk import RiskAssessmentContract


class AlertNotFoundError(LookupError):
    """Raised when an alert ID does not exist."""


class AlertService:
    """Generates, persists, and manages operational alerts distinct from official warnings."""

    def __init__(self, repo: AlertRepository) -> None:
        self._repo = repo

    @staticmethod
    def _build_recommendation(
        hazard_type: HazardType, priority: PriorityAssessment
    ) -> str:
        if hazard_type == HazardType.FLOOD:
            if priority.priority_level in {"CRITICAL", "HIGH"}:
                return (
                    "Activate river gauge watch, inspect low-lying drainage/bridges, "
                    "and pre-position SDRF flood response teams."
                )
            return "Maintain routine rainfall and river gauge monitoring."
        if priority.priority_level in {"CRITICAL", "HIGH"}:
            return (
                "Restrict high-altitude corridor movement, verify snowpack stability, "
                "and alert avalanche control posts."
            )
        return "Maintain snowpack and weather watch; note readiness/coverage constraints."

    def generate_for_assessment(
        self,
        assessment: RiskAssessmentContract,
        priority: PriorityAssessment,
    ) -> AlertActionRecord | None:
        """Generate and persist an operational alert when risk/priority warrants action."""
        if (
            assessment.prediction_status == PredictionStatus.UNSUPPORTED
            or assessment.risk_class == RiskClass.UNSUPPORTED
            or priority.prediction_status == PredictionStatus.UNSUPPORTED
            or priority.hazard_risk_class == RiskClass.UNSUPPORTED
        ):
            return None
        if priority.priority_level not in {"MEDIUM", "HIGH", "CRITICAL"}:
            return None

        title = (
            f"{priority.priority_level} {assessment.hazard_type.value.title()} Alert — "
            f"{assessment.location_id}"
        )
        recommendation = self._build_recommendation(assessment.hazard_type, priority)
        record = AlertActionRecord(
            alert_id=f"alert-{assessment.hazard_type.value}-{uuid4().hex[:10]}",
            location_id=assessment.location_id,
            hazard_type=assessment.hazard_type,
            risk_id=assessment.risk_id,
            priority_level=priority.priority_level,
            priority_score=priority.priority_score,
            title=title,
            recommendation=recommendation,
            explanation=list(priority.explanation),
            status=AlertStatus.ACTIVE,
            is_official_warning=False,
            created_at=datetime.now(UTC),
        )
        return self._repo.create(record)

    def list_alerts(
        self,
        location_id: str | None = None,
        status: AlertStatus | None = None,
        hazard_type: HazardType | None = None,
    ) -> list[AlertActionRecord]:
        return self._repo.list_alerts(
            location_id=location_id,
            status=status,
            hazard_type=hazard_type,
        )

    def acknowledge_alert(
        self,
        alert_id: str,
        actor_username: str,
        note: str | None = None,
    ) -> AlertActionRecord:
        existing = self._repo.get_by_id(alert_id)
        if existing is None:
            raise AlertNotFoundError(f"Alert '{alert_id}' not found.")
        updated = self._repo.update_status(
            alert_id,
            AlertStatus.ACKNOWLEDGED,
            acknowledged_by=actor_username,
            acknowledged_at=datetime.now(UTC),
            action_note=note if note is not None else existing.action_note,
        )
        assert updated is not None
        return updated

    def update_action_status(
        self,
        alert_id: str,
        status: AlertStatus,
        action_note: str | None = None,
    ) -> AlertActionRecord:
        existing = self._repo.get_by_id(alert_id)
        if existing is None:
            raise AlertNotFoundError(f"Alert '{alert_id}' not found.")
        updated = self._repo.update_status(
            alert_id,
            status,
            action_note=action_note if action_note is not None else existing.action_note,
        )
        assert updated is not None
        return updated
