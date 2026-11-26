"""ORM model for authoritative read-only official warnings."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OfficialWarningModel(Base):
    """Authoritative warning issued by an external agency (CWC, IMD, DGRE, SDMA)."""

    __tablename__ = "official_warnings"

    warning_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    authority: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    hazard_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("locations.location_id"),
        nullable=False,
        index=True,
    )
    severity_label: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(240), nullable=False)
    geographic_scope: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    advisory_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    is_read_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    provenance: Mapped[str] = mapped_column(String(160), nullable=False)
    is_demo_fixture: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @property
    def is_expired(self) -> bool:
        """Return True if the warning validity window has passed."""
        now = datetime.now(UTC)
        valid = self.valid_until if self.valid_until.tzinfo else self.valid_until.replace(tzinfo=UTC)
        return now >= valid
