"""Repository for pilot location records."""

from functools import lru_cache

from app.models.location import CoverageStatus, HazardType, LocationRecord


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


@lru_cache
def get_location_repository() -> LocationRepository:
    """Return a singleton repository seeded with deterministic pilot fixtures."""
    from app.seed.locations import seed_locations

    repo = LocationRepository()
    seed_locations(repo)
    return repo
