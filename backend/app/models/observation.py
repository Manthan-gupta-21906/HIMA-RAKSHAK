"""ORM model for validated environmental observations."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ObservationModel(Base):
    """Persistent time-series observation tied to a location and source."""

    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint(
            "location_id",
            "source_id",
            "observed_at",
            "metric",
            name="uq_observations_natural_key",
        ),
    )

    observation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    location_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("locations.location_id"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("sources.source_id"),
        nullable=False,
        index=True,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    metric: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    is_demo_fixture: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
