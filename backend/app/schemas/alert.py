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
