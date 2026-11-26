"""ORM model for system-generated alerts and operator action history.

Distinct from OfficialWarningModel (authoritative CWC/DGRE/IMD bulletins).
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AlertActionModel(Base):
    """Persistent system-generated alert with recommendation, acknowledgement, and action status."""

    __tablename__ = "alerts"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    location_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("locations.location_id"),
        nullable=False,
        index=True,
    )
    hazard_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    risk_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("risk_assessments.risk_id"),
        nullable=True,
        index=True,
    )
    priority_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    action_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_official_warning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivery_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class AlertDeliveryModel(Base):
    """Persistent delivery attempt record for an operational alert."""

    __tablename__ = "alert_deliveries"

    delivery_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    alert_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("alerts.alert_id"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
