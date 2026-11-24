"""Source registry API routes."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.models.source import SourceModel  # noqa: F401
from app.repositories.source_repository import SourceNotFoundError, SourceRepository
from app.schemas.source import (
    AccessMode,
    SourceContract,
    SourceListResponse,
    SourceResponse,
    SourceType,
)
from app.services.source_service import SourceService

router = APIRouter(prefix="/sources", tags=["sources"])

_engine = create_db_engine()
Base.metadata.create_all(bind=_engine)
_session_factory = get_session_factory(_engine)


def _get_db() -> Generator[Session, None, None]:
    db = _session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _get_service(db: Session = Depends(_get_db)) -> SourceService:
    return SourceService(SourceRepository(db))


@router.get("", response_model=SourceListResponse)
def list_sources(
    source_type: SourceType | None = Query(None),
    access_mode: AccessMode | None = Query(None),
    service: SourceService = Depends(_get_service),
) -> SourceListResponse:
    """List registered data sources with optional filters."""
    items = service.list_sources(
        source_type=source_type.value if source_type else None,
        access_mode=access_mode.value if access_mode else None,
    )
    return SourceListResponse(total=len(items), items=items)


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: str,
    service: SourceService = Depends(_get_service),
) -> SourceResponse:
    """Get details for a single data source."""
    try:
        return service.get_source(source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "", response_model=SourceResponse, status_code=status.HTTP_201_CREATED
)
def register_source(
    payload: SourceContract,
    _admin: object = Depends(require_admin),
    service: SourceService = Depends(_get_service),
) -> SourceResponse:
    """Register a new data source (admin only)."""
    return service.register_source(payload)


@router.post(
    "/{source_id}/fetch",
    response_model=SourceResponse,
)
def record_fetch(
    source_id: str,
    _admin: object = Depends(require_admin),
    service: SourceService = Depends(_get_service),
) -> SourceResponse:
    """Record that data was fetched from this source (admin only)."""
    try:
        return service.record_fetch(source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
