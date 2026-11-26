"""Location catalogue API routes with pagination, search, and role enforcement."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.models.location import CoverageStatus, HazardType
from app.models.user import UserRole
from app.repositories.location_repository import (
    LocationRepository,
    get_location_repository,
)
from app.schemas.common import PaginationMeta
from app.schemas.location import (
    LocationCoverageUpdate,
    LocationCreate,
    LocationListResponse,
    LocationOut,
)
from app.services.location_service import LocationNotFoundError, LocationService

router = APIRouter(prefix="/locations", tags=["locations"])

oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_location_service(
    repo: LocationRepository = Depends(get_location_repository),
) -> LocationService:
    return LocationService(repo)


def require_admin_or_header(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    token: str | None = Depends(oauth2_optional),
) -> str:
    """Enforce admin role via X-User-Role header or Bearer JWT token."""
    if token:
        try:
            payload = decode_access_token(token)
            role = payload.get("role")
            if role in (UserRole.ADMIN.value, UserRole.ADMIN):
                return "admin"
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required to modify pilot locations.",
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials.",
            ) from exc

    if x_user_role is not None:
        if x_user_role.lower() == "admin":
            return "admin"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to modify pilot locations.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials or X-User-Role header required.",
    )


@router.get("", response_model=LocationListResponse)
def list_locations(
    q: str | None = Query(default=None, description="Search by ID, name, or admin unit"),
    hazard_type: HazardType | None = Query(default=None, description="Filter by supported hazard"),
    coverage_status: CoverageStatus | None = Query(
        default=None, description="Filter by coverage status"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    service: LocationService = Depends(get_location_service),
) -> LocationListResponse:
    """List or search curated pilot locations with pagination."""
    records = service.list_locations(
        query=q,
        hazard_type=hazard_type,
        coverage_status=coverage_status,
    )
    total = len(records)
    start_idx = (page - 1) * page_size
    paged_records = records[start_idx : start_idx + page_size]
    items = [LocationOut(**asdict(r)) for r in paged_records]
    has_next = (start_idx + page_size) < total

    return LocationListResponse(
        total=total,
        items=items,
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        ),
    )


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
    _role: str = Depends(require_admin_or_header),
    service: LocationService = Depends(get_location_service),
) -> LocationOut:
    """Register a new pilot location (admin only)."""
    record = service.create_location(payload)
    return LocationOut(**asdict(record))


@router.patch("/{location_id}/coverage", response_model=LocationOut)
def update_location_coverage(
    location_id: str,
    payload: LocationCoverageUpdate,
    _role: str = Depends(require_admin_or_header),
    service: LocationService = Depends(get_location_service),
) -> LocationOut:
    """Update coverage status for a pilot location (admin only)."""
    try:
        record = service.update_coverage(location_id, payload)
    except LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return LocationOut(**asdict(record))
