"""Observations API routes — paginated, filterable, role-enforced."""

from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_any_authenticated, require_operator
from app.db.session import get_db
from app.models.location import LocationModel  # noqa: F401
from app.models.observation import ObservationModel  # noqa: F401
from app.models.source import SourceModel  # noqa: F401
from app.repositories.observation_repository import ObservationRepository
from app.schemas.common import PaginationMeta
from app.schemas.observation import (
    ObservationContract,
    ObservationCreate,
    ObservationListResponse,
    ObservationMetric,
)
from app.services.observation_service import (
    IncompatibleHazardError,
    LocationNotFoundError,
    ObservationService,
)

router = APIRouter(prefix="/observations", tags=["observations"])


def _get_db() -> Generator[Session, None, None]:
    yield from get_db()


def get_observation_service(db: Session = Depends(_get_db)) -> ObservationService:
    return ObservationService(ObservationRepository(db))


@router.post("", response_model=ObservationContract, status_code=status.HTTP_201_CREATED)
def create_observation(
    payload: ObservationCreate,
    _user: object = Depends(require_operator),
    service: ObservationService = Depends(get_observation_service),
) -> ObservationContract:
    """Submit a field or telemetry observation. Requires operator or admin role."""
    try:
        return service.create_observation(payload)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location not found: {exc}",
        ) from exc
    except IncompatibleHazardError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("", response_model=ObservationListResponse)
def list_observations(
    location_id: str = Query(..., min_length=2, description="Location ID to filter observations"),
    metric: ObservationMetric | None = Query(
        default=None, description="Filter by observation metric"
    ),
    since: datetime | None = Query(
        default=None, description="Include only observations on or after this timestamp (ISO 8601)"
    ),
    until: datetime | None = Query(
        default=None, description="Include only observations on or before this timestamp (ISO 8601)"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    _user: object = Depends(require_any_authenticated),
    service: ObservationService = Depends(get_observation_service),
) -> ObservationListResponse:
    """List environmental observations for a location with pagination and filters."""
    items, total = service.list_observations(
        location_id=location_id,
        metric=metric,
        since=since,
        until=until,
        page=page,
        page_size=page_size,
    )
    start_idx = (page - 1) * page_size
    has_next = (start_idx + page_size) < total

    return ObservationListResponse(
        total=total,
        items=items,
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        ),
    )

