"""Repository for persisting system-generated alerts, deliveries, and action history."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import AlertActionModel, AlertDeliveryModel
from app.schemas.alert import (
    AlertActionRecord,
    AlertDeliveryRecord,
    AlertStatus,
    DeliveryChannel,
    DeliveryStatus,
)
from app.schemas.common import HazardType


class AlertRepository:
    """SQLAlchemy-backed repository for operational alerts and action history."""

    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def _ensure_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    @classmethod
    def _delivery_to_contract(cls, row: AlertDeliveryModel) -> AlertDeliveryRecord:
        return AlertDeliveryRecord(
            delivery_id=row.delivery_id,
            alert_id=row.alert_id,
            channel=DeliveryChannel(row.channel),
            target=row.target,
            status=DeliveryStatus(row.status),
            attempts=row.attempts,
            response_code=row.response_code,
            last_error=row.last_error,
            dispatched_at=cls._ensure_utc(row.dispatched_at),
            created_at=cls._ensure_utc(row.created_at) or datetime.now(UTC),
        )

    def _to_contract(self, row: AlertActionModel) -> AlertActionRecord:
        deliveries = self.list_deliveries(row.alert_id)
        return AlertActionRecord(
            alert_id=row.alert_id,
            location_id=row.location_id,
            hazard_type=HazardType(row.hazard_type),
            risk_id=row.risk_id,
            priority_level=row.priority_level,
            priority_score=row.priority_score,
            title=row.title,
            recommendation=row.recommendation,
            explanation=list(row.explanation or []),
            status=AlertStatus(row.status),
            delivery_status=DeliveryStatus(row.delivery_status),
            deliveries=deliveries,
            acknowledged_by=row.acknowledged_by,
            acknowledged_at=self._ensure_utc(row.acknowledged_at),
            action_note=row.action_note,
            action_updated_at=self._ensure_utc(row.action_updated_at),
            is_official_warning=bool(row.is_official_warning),
            created_at=self._ensure_utc(row.created_at) or datetime.now(UTC),
        )

    def create(self, record: AlertActionRecord) -> AlertActionRecord:
        """Persist a new operational alert record."""
        model = AlertActionModel(
            alert_id=record.alert_id,
            location_id=record.location_id,
            hazard_type=record.hazard_type.value,
            risk_id=record.risk_id,
            priority_level=record.priority_level,
            priority_score=record.priority_score,
            title=record.title,
            recommendation=record.recommendation,
            explanation=list(record.explanation),
            status=record.status.value,
            delivery_status=record.delivery_status.value,
            acknowledged_by=record.acknowledged_by,
            acknowledged_at=record.acknowledged_at,
            action_note=record.action_note,
            action_updated_at=record.action_updated_at,
            is_official_warning=False,
            created_at=record.created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_contract(model)

    def get_by_id(self, alert_id: str) -> AlertActionRecord | None:
        """Fetch an alert by ID."""
        row = self._db.get(AlertActionModel, alert_id)
        return self._to_contract(row) if row is not None else None

    def list_alerts(
        self,
        location_id: str | None = None,
        status: AlertStatus | None = None,
        hazard_type: HazardType | None = None,
    ) -> list[AlertActionRecord]:
        """List persisted alerts ordered newest-first."""
        stmt = select(AlertActionModel)
        if location_id:
            stmt = stmt.where(AlertActionModel.location_id == location_id)
        if status:
            stmt = stmt.where(AlertActionModel.status == status.value)
        if hazard_type:
            stmt = stmt.where(AlertActionModel.hazard_type == hazard_type.value)
        stmt = stmt.order_by(AlertActionModel.created_at.desc())
        rows = self._db.scalars(stmt).all()
        return [self._to_contract(r) for r in rows]

    def update_status(
        self,
        alert_id: str,
        status: AlertStatus,
        *,
        acknowledged_by: str | None = None,
        acknowledged_at: datetime | None = None,
        action_note: str | None = None,
    ) -> AlertActionRecord | None:
        """Update acknowledgement and action status on an existing alert."""
        row = self._db.get(AlertActionModel, alert_id)
        if row is None:
            return None
        row.status = status.value
        if acknowledged_by is not None:
            row.acknowledged_by = acknowledged_by
        if acknowledged_at is not None:
            row.acknowledged_at = acknowledged_at
        if action_note is not None:
            row.action_note = action_note
        row.action_updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(row)
        return self._to_contract(row)

    def record_deliveries(
        self,
        alert_id: str,
        deliveries: list[AlertDeliveryRecord],
        overall_status: DeliveryStatus,
    ) -> AlertActionRecord | None:
        """Persist delivery attempts and update the alert's overall delivery_status."""
        row = self._db.get(AlertActionModel, alert_id)
        if row is None:
            return None
        for d in deliveries:
            self._db.add(
                AlertDeliveryModel(
                    delivery_id=d.delivery_id,
                    alert_id=d.alert_id,
                    channel=d.channel.value,
                    target=d.target,
                    status=d.status.value,
                    attempts=d.attempts,
                    response_code=d.response_code,
                    last_error=d.last_error,
                    dispatched_at=d.dispatched_at,
                    created_at=d.created_at,
                )
            )
        row.delivery_status = overall_status.value
        self._db.commit()
        self._db.refresh(row)
        return self._to_contract(row)

    def list_deliveries(self, alert_id: str) -> list[AlertDeliveryRecord]:
        """List delivery attempts for an alert ordered newest-first."""
        stmt = (
            select(AlertDeliveryModel)
            .where(AlertDeliveryModel.alert_id == alert_id)
            .order_by(AlertDeliveryModel.created_at.desc())
        )
        rows = self._db.scalars(stmt).all()
        return [self._delivery_to_contract(r) for r in rows]
