"""Location catalogue API routes."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.models.location import CoverageStatus, HazardType
from app.repositories.location_repository import (
    LocationRepository,
    get_location_repository,
)
from app.schemas.location import (
    LocationCoverageUpdate,
    LocationCreate,
    LocationListResponse,
    LocationOut,
)
from app.services.location_service import LocationNotFoundError, LocationService

router = APIRouter(prefix="/locations", tags=["locations"])


def get_location_service(
    repo: LocationRepository = Depends(get_location_repository),
) -> LocationService:
    return LocationService(repo)


def require_admin_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> str:
    """Enforce role policy for protected location write endpoints."""
    if not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Role header.",
        )
    if x_user_role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to modify pilot locations.",
        )
    return x_user_role.lower()


@router.get("", response_model=LocationListResponse)
def list_locations(
    q: str | None = Query(default=None, description="Search by ID, name, or admin unit"),
    hazard_type: HazardType | None = Query(default=None),
    coverage_status: CoverageStatus | None = Query(default=None),
    service: LocationService = Depends(get_location_service),
) -> LocationListResponse:
    """List or search curated pilot locations."""
    records = service.list_locations(
        query=q,
        hazard_type=hazard_type,
        coverage_status=coverage_status,
    )
    items = [LocationOut(**asdict(r)) for r in records]
    return LocationListResponse(total=len(items), items=items)


@router.get("/{location_id}", response_model=LocationOut)
def get_location_detail(
    location_id: str,
    service: LocationService = Depends(get_location_service),
) -> LocationOut:
    """Get details for a single pilot location."""
    try:
        record = service.get_location(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return LocationOut(**asdict(record))


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreate,
    _role: str = Depends(require_admin_role),
    service: LocationService = Depends(get_location_service),
) -> LocationOut:
    """Register a new pilot location (admin only)."""
    record = service.create_location(payload)
    return LocationOut(**asdict(record))


@router.patch("/{location_id}/coverage", response_model=LocationOut)
def update_location_coverage(
    location_id: str,
    payload: LocationCoverageUpdate,
    _role: str = Depends(require_admin_role),
    service: LocationService = Depends(get_location_service),
) -> LocationOut:
    """Update coverage status for a pilot location (admin only)."""
    try:
        record = service.update_coverage(location_id, payload)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return LocationOut(**asdict(record))
