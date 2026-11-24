"""ORM model for data source provenance."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SourceModel(Base):
    """Persistent metadata for environmental and official warning sources."""

    __tablename__ = "sources"

    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    licence: Mapped[str] = mapped_column(String(120), nullable=False)
    update_frequency_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo_fixture: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
