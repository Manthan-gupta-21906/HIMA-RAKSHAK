"""Repository for pilot location records."""

from functools import lru_cache
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.location import CoverageStatus, HazardType, LocationModel, LocationRecord


class LocationRepository:
    """In-memory repository for pilot locations (swappable for PostGIS later)."""

    def __init__(self) -> None:
        self._items: dict[str, LocationRecord] = {}

    def list_all(self) -> list[LocationRecord]:
        return list(self._items.values())

    def get_by_id(self, location_id: str) -> LocationRecord | None:
        return self._items.get(location_id)

    def search(
        self,
        query: str | None = None,
        hazard_type: HazardType | None = None,
        coverage_status: CoverageStatus | None = None,
    ) -> list[LocationRecord]:
        results = self.list_all()
        if query:
            needle = query.strip().lower()
            results = [
                loc
                for loc in results
                if needle in loc.name.lower()
                or needle in loc.admin_unit.lower()
                or needle in loc.location_id.lower()
            ]
        if hazard_type:
            results = [loc for loc in results if hazard_type in loc.supported_hazards]
        if coverage_status:
            results = [loc for loc in results if loc.coverage_status == coverage_status]
        return results

    def upsert(self, location: LocationRecord) -> LocationRecord:
        self._items[location.location_id] = location
        return location

    def count(self) -> int:
        return len(self._items)


class SqlAlchemyLocationRepository:
    """SQLAlchemy/PostGIS-backed repository for pilot locations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def _to_record(row: LocationModel) -> LocationRecord:
        return LocationRecord(
            location_id=row.location_id,
            name=row.name,
            admin_unit=row.admin_unit,
            latitude=row.latitude,
            longitude=row.longitude,
            geometry_geojson=dict(row.geom),
            supported_hazards=cast(list[HazardType], list(row.supported_hazards)),
            coverage_status=cast(CoverageStatus, row.coverage_status),
            coverage_note=row.coverage_note,
            is_demo_fixture=row.is_demo_fixture,
            provenance=row.provenance,
        )

    def upsert(self, location: LocationRecord) -> LocationRecord:
        geom = location.geometry_geojson or {
            "type": "Point",
            "coordinates": [location.longitude, location.latitude],
        }
        row = self._db.get(LocationModel, location.location_id)
        if row is None:
            row = LocationModel(
                location_id=location.location_id,
                name=location.name,
                admin_unit=location.admin_unit,
                latitude=location.latitude,
                longitude=location.longitude,
                geom=geom,
                supported_hazards=list(location.supported_hazards),
                coverage_status=location.coverage_status,
                coverage_note=location.coverage_note,
                is_demo_fixture=location.is_demo_fixture,
                provenance=location.provenance,
            )
            self._db.add(row)
        else:
            row.name = location.name
            row.admin_unit = location.admin_unit
            row.latitude = location.latitude
            row.longitude = location.longitude
            row.geom = geom
            row.supported_hazards = list(location.supported_hazards)
            row.coverage_status = location.coverage_status
            row.coverage_note = location.coverage_note
        self._db.flush()
        return self._to_record(row)

    def get_by_id(self, location_id: str) -> LocationRecord | None:
        row = self._db.get(LocationModel, location_id)
        return self._to_record(row) if row else None

    def list_all(self) -> list[LocationRecord]:
        rows = self._db.scalars(select(LocationModel)).all()
        return [self._to_record(r) for r in rows]

    def count(self) -> int:
        return int(self._db.scalar(select(func.count()).select_from(LocationModel)) or 0)


@lru_cache
def get_location_repository() -> LocationRepository:
    """Return a singleton repository seeded with deterministic pilot fixtures."""
    from app.seed.locations import seed_locations

    repo = LocationRepository()
    seed_locations(repo)
    return repo
