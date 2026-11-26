"""ORM model for system-generated alerts and operator action history.

Distinct from OfficialWarningModel (authoritative CWC/DGRE/IMD bulletins).
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
