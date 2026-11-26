"""Observations API routes — paginated, filterable, role-enforced."""

from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_any_authenticated
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.models.observation import ObservationModel  # noqa: F401
from app.repositories.observation_repository import ObservationRepository
from app.schemas.common import PaginationMeta
from app.schemas.observation import (
    ObservationListResponse,
    ObservationMetric,
)
from app.services.observation_service import ObservationService

router = APIRouter(prefix="/observations", tags=["observations"])

_engine = create_db_engine()
Base.metadata.create_all(bind=_engine)
_session_factory = get_session_factory(_engine)


def get_db() -> Generator[Session, None, None]:
    db = _session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_observation_service(db: Session = Depends(get_db)) -> ObservationService:
    return ObservationService(ObservationRepository(db))


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
