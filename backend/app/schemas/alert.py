"""Contracts for system-generated alerts, recommendations, and operator action history."""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import AwareDatetime, HazardType


class AlertStatus(StrEnum):
    """Lifecycle status of a system-generated operational alert."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class DeliveryStatus(StrEnum):
    """Delivery status of an operational alert across notification channels."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class DeliveryChannel(StrEnum):
    """Supported operational alert delivery channels."""

    WEBHOOK = "webhook"
    EMAIL = "email"
    CONSOLE = "console"


class AlertDeliveryRecord(BaseModel):
    """Persisted delivery attempt and status for a system alert."""

    delivery_id: str
    alert_id: str
    channel: DeliveryChannel
    target: str
    status: DeliveryStatus
    attempts: int = 1
    response_code: int | None = None
    last_error: str | None = None
    dispatched_at: AwareDatetime | None = None
    created_at: AwareDatetime


class AlertDeliveryListResponse(BaseModel):
    """Response envelope for listing alert delivery attempts."""

    alert_id: str
    delivery_status: DeliveryStatus
    total: int
    items: list[AlertDeliveryRecord]


class DeliverAlertRequest(BaseModel):
    """Optional payload to trigger or retry alert delivery."""

    channels: list[DeliveryChannel] | None = None
    webhook_url: str | None = Field(default=None, max_length=500)
    email_recipients: list[str] | None = None


class AlertActionRecord(BaseModel):
    """Persisted system alert distinct from authoritative CWC/DGRE/IMD warnings."""

    alert_id: str
    location_id: str
    hazard_type: HazardType
    risk_id: str | None = None
    priority_level: str
    priority_score: float = Field(ge=0.0, le=1.0)
    title: str
    recommendation: str
    explanation: list[str] = Field(default_factory=list)
    status: AlertStatus = AlertStatus.ACTIVE
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    deliveries: list[AlertDeliveryRecord] = Field(default_factory=list)
    acknowledged_by: str | None = None
    acknowledged_at: AwareDatetime | None = None
    action_note: str | None = None
    action_updated_at: AwareDatetime | None = None
    is_official_warning: bool = False
    created_at: AwareDatetime


class AlertListResponse(BaseModel):
    """Response envelope for listing system-generated alerts."""

    total: int
    items: list[AlertActionRecord]


class AcknowledgeAlertRequest(BaseModel):
    """Payload to acknowledge a system alert."""

    note: str | None = Field(default=None, max_length=500)


class UpdateAlertActionRequest(BaseModel):
    """Payload to update action status and operator notes on an alert."""

    status: AlertStatus
    action_note: str | None = Field(default=None, max_length=500)
