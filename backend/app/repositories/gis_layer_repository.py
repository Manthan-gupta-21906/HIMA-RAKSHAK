"""Repository for persisting and querying managed GIS layers."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gis_layer import ManagedGisLayerModel
from app.schemas.layer import LayerCategory, ManagedLayerDetail, ManagedLayerSummary


class GisLayerRepository:
    """SQLAlchemy-backed repository for managed GIS layers."""

    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def _ensure_utc(dt: datetime | None) -> datetime:
        if dt is None:
            return datetime.now(UTC)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    @classmethod
    def _to_summary(cls, row: ManagedGisLayerModel) -> ManagedLayerSummary:
        return ManagedLayerSummary(
            layer_id=row.layer_id,
            name=row.name,
            layer_category=LayerCategory(row.layer_category),
            description=row.description,
            provenance=row.provenance,
            is_demo_fixture=bool(row.is_demo_fixture),
            source_crs_epsg=row.source_crs_epsg,
            feature_count=row.feature_count,
            is_active=bool(row.is_active),
            created_at=cls._ensure_utc(row.created_at),
            updated_at=cls._ensure_utc(row.updated_at),
        )

    @classmethod
    def _to_detail(cls, row: ManagedGisLayerModel) -> ManagedLayerDetail:
        return ManagedLayerDetail(
            **cls._to_summary(row).model_dump(),
            geojson=row.geojson,
        )

    def upsert_layer(
        self,
        *,
        layer_id: str,
        name: str,
        layer_category: str,
        description: str,
        provenance: str,
        is_demo_fixture: bool,
        source_crs_epsg: int,
        feature_count: int,
        geojson: dict[str, Any],
        is_active: bool = True,
    ) -> ManagedLayerDetail:
        """Create or update a managed GIS layer."""
        now = datetime.now(UTC)
        existing = self._db.get(ManagedGisLayerModel, layer_id)
        if existing is not None:
            existing.name = name
            existing.layer_category = layer_category
            existing.description = description
            existing.provenance = provenance
            existing.is_demo_fixture = is_demo_fixture
            existing.source_crs_epsg = source_crs_epsg
            existing.feature_count = feature_count
            existing.geojson = geojson
            existing.is_active = is_active
            existing.updated_at = now
            self._db.commit()
            self._db.refresh(existing)
            return self._to_detail(existing)

        row = ManagedGisLayerModel(
            layer_id=layer_id,
            name=name,
            layer_category=layer_category,
            description=description,
            provenance=provenance,
            is_demo_fixture=is_demo_fixture,
            source_crs_epsg=source_crs_epsg,
            feature_count=feature_count,
            geojson=geojson,
            is_active=is_active,
            created_at=now,
            updated_at=now,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return self._to_detail(row)

    def get_by_id(self, layer_id: str) -> ManagedLayerDetail | None:
        """Fetch a managed GIS layer by ID."""
        row = self._db.get(ManagedGisLayerModel, layer_id)
        return self._to_detail(row) if row is not None else None

    def list_layers(
        self,
        *,
        category: str | None = None,
        active_only: bool = True,
    ) -> list[ManagedLayerSummary]:
        """List managed GIS layers."""
        stmt = select(ManagedGisLayerModel)
        if category is not None:
            stmt = stmt.where(ManagedGisLayerModel.layer_category == category)
        if active_only:
            stmt = stmt.where(ManagedGisLayerModel.is_active.is_(True))
        stmt = stmt.order_by(ManagedGisLayerModel.layer_id.asc())
        rows = self._db.scalars(stmt).all()
        return [self._to_summary(r) for r in rows]

    def list_layer_details(
        self,
        *,
        category: str | None = None,
        active_only: bool = True,
    ) -> list[ManagedLayerDetail]:
        """List managed GIS layers including their GeoJSON payloads."""
        stmt = select(ManagedGisLayerModel)
        if category is not None:
            stmt = stmt.where(ManagedGisLayerModel.layer_category == category)
        if active_only:
            stmt = stmt.where(ManagedGisLayerModel.is_active.is_(True))
        stmt = stmt.order_by(ManagedGisLayerModel.layer_id.asc())
        rows = self._db.scalars(stmt).all()
        return [self._to_detail(r) for r in rows]

    def deactivate_layer(self, layer_id: str) -> bool:
        """Soft-deactivate a managed GIS layer."""
        row = self._db.get(ManagedGisLayerModel, layer_id)
        if row is None:
            return False
        row.is_active = False
        row.updated_at = datetime.now(UTC)
        self._db.commit()
        return True
