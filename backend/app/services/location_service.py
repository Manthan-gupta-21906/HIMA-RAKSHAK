"""Business logic for the pilot location catalogue."""

from app.models.location import CoverageStatus, HazardType, LocationRecord
from app.repositories.location_repository import LocationRepository
from app.schemas.location import LocationCoverageUpdate, LocationCreate


class LocationNotFoundError(Exception):
    """Raised when a requested location_id does not exist."""


class LocationService:
    """Service layer for querying and managing pilot locations."""

    def __init__(self, repo: LocationRepository) -> None:
        self._repo = repo

    def list_locations(
        self,
        query: str | None = None,
        hazard_type: HazardType | None = None,
        coverage_status: CoverageStatus | None = None,
    ) -> list[LocationRecord]:
        return self._repo.search(
            query=query,
            hazard_type=hazard_type,
            coverage_status=coverage_status,
        )

    def get_location(self, location_id: str) -> LocationRecord:
        loc = self._repo.get_by_id(location_id)
        if loc is None:
            raise LocationNotFoundError(f"Location '{location_id}' not found.")
        return loc

    def create_location(self, payload: LocationCreate) -> LocationRecord:
        record = LocationRecord(
            location_id=payload.location_id,
            name=payload.name,
            admin_unit=payload.admin_unit,
            latitude=payload.latitude,
            longitude=payload.longitude,
            geometry_geojson={
                "type": "Point",
                "coordinates": [payload.longitude, payload.latitude],
            },
            supported_hazards=payload.supported_hazards,
            coverage_status=payload.coverage_status,
            coverage_note=payload.coverage_note,
        )
        return self._repo.upsert(record)

    def update_coverage(
        self, location_id: str, payload: LocationCoverageUpdate
    ) -> LocationRecord:
        loc = self.get_location(location_id)
        loc.coverage_status = payload.coverage_status
        loc.coverage_note = payload.coverage_note
        return self._repo.upsert(loc)
