"""ORM model for managed geospatial (GIS) layers stored in the database."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ManagedGisLayerModel(Base):
    """Persistent managed GIS vector layer normalized to EPSG:4326."""

    __tablename__ = "managed_gis_layers"

    layer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    layer_category: Mapped[str] = mapped_column(
        String(32), nullable=False, default="exposure", index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provenance: Mapped[str] = mapped_column(String(200), nullable=False)
    is_demo_fixture: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source_crs_epsg: Mapped[int] = mapped_column(Integer, default=4326, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    geojson: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
