"""ORM model for multi-hazard risk assessments."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskAssessmentModel(Base):
    """Persistent risk assessment state emitted by a distinct hazard pathway."""

    __tablename__ = "risk_assessments"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "hazard_type",
            "assessed_at",
            name="uq_risk_assessment_location_hazard_time",
        ),
    )

    risk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    location_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("locations.location_id"),
        nullable=False,
        index=True,
    )
    hazard_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    risk_class: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    lead_time_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    freshness: Mapped[str] = mapped_column(String(32), nullable=False)
    prediction_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    readiness_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Provenance fields
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    licence: Mapped[str] = mapped_column(String(120), nullable=False)
    is_demo_fixture: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
