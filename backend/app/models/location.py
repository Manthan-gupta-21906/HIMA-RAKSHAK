"""Domain and ORM models for curated pilot locations."""

from dataclasses import dataclass, field
from typing import Any, Literal

from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from shapely.wkt import dumps as wkt_dumps
from shapely.wkt import loads as wkt_loads
from sqlalchemy import JSON, Boolean, Float, String, Text
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.db.base import Base

HazardType = Literal["flood", "avalanche"]
CoverageStatus = Literal["supported", "partial", "unsupported"]


class SpatialPoint(TypeDecorator[dict[str, Any]]):
    """PostGIS GEOMETRY(POINT, 4326) on PostgreSQL, WKT Text fallback on SQLite."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geometry("POINT", srid=4326))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: dict[str, Any] | None, dialect: Dialect) -> Any:
        if value is None:
            return None
        coords = value["coordinates"]
        pt = Point(float(coords[0]), float(coords[1]))
        if dialect.name == "postgresql":
            return from_shape(pt, srid=4326)
        return wkt_dumps(pt)

    def process_result_value(self, value: Any, dialect: Dialect) -> dict[str, Any] | None:
        if value is None:
            return None
        pt = wkt_loads(value) if isinstance(value, str) else to_shape(value)
        return {"type": "Point", "coordinates": [pt.x, pt.y]}


@dataclass
class LocationRecord:
    """Pilot location entity with spatial coordinates, hazard support, and coverage."""

    location_id: str
    name: str
    admin_unit: str
    latitude: float
    longitude: float
    supported_hazards: list[HazardType]
    coverage_status: CoverageStatus
    coverage_note: str
    geometry_geojson: dict[str, object] = field(default_factory=dict)
    is_demo_fixture: bool = True
    provenance: str = "demo_fixture:round1_jk_pilot"


class LocationModel(Base):
    """Persistent pilot location entity with spatial geometry."""

    __tablename__ = "locations"

    location_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    admin_unit: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    geom: Mapped[dict[str, Any]] = mapped_column(SpatialPoint(), nullable=False)
    supported_hazards: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    coverage_status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    coverage_note: Mapped[str] = mapped_column(Text, nullable=False)
    is_demo_fixture: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    provenance: Mapped[str] = mapped_column(String(120), nullable=False)
