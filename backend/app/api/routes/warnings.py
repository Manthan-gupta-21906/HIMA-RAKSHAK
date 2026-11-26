"""Official warning API routes — read-only access for ordinary roles, curation for operators."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_any_authenticated, require_operator
from app.db.session import get_db
from app.ingestion.warning_import import import_sample_fixtures
from app.models.location import LocationModel  # noqa: F401
from app.models.official_warning import OfficialWarningModel  # noqa: F401
from app.repositories.warning_repository import OfficialWarningRepository
from app.schemas.common import HazardType, PaginationMeta
from app.schemas.warning import (
    OfficialWarningContract,
    WarningAuthority,
    WarningCreate,
    WarningListResponse,
)

router = APIRouter(prefix="/warnings", tags=["warnings"])


def _get_db() -> Generator[Session, None, None]:
    yield from get_db()


def get_warning_repository(db: Session = Depends(_get_db)) -> OfficialWarningRepository:
    return OfficialWarningRepository(db)


@router.get("", response_model=WarningListResponse)
def list_warnings(
    location_id: str | None = Query(default=None, description="Filter by location identifier"),
    hazard_type: HazardType | None = Query(default=None, description="Filter by hazard type"),
    authority: WarningAuthority | None = Query(
        default=None, description="Filter by issuing authority"
    ),
    is_expired: bool | None = Query(default=None, description="Filter by expiration status"),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    _user: object = Depends(require_any_authenticated),
    repo: OfficialWarningRepository = Depends(get_warning_repository),
) -> WarningListResponse:
    """List official warnings preserving authority, validity, and read-only provenance."""
    models, total = repo.list_warnings(
        location_id=location_id,
        hazard_type=hazard_type.value if hazard_type else None,
        authority=authority.value if authority else None,
        is_expired=is_expired,
        page=page,
        page_size=page_size,
    )
    items = [repo.to_contract(m) for m in models]
    start_idx = (page - 1) * page_size
    has_next = (start_idx + page_size) < total

    return WarningListResponse(
        total=total,
        items=items,
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        ),
    )


@router.get("/{warning_id}", response_model=OfficialWarningContract)
def get_warning(
    warning_id: str,
    _user: object = Depends(require_any_authenticated),
    repo: OfficialWarningRepository = Depends(get_warning_repository),
) -> OfficialWarningContract:
    """Fetch an authoritative official warning record by its identifier."""
    model = repo.get_by_id(warning_id)
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Official warning not found: {warning_id}",
        )
    return repo.to_contract(model)


@router.post("", response_model=OfficialWarningContract, status_code=status.HTTP_201_CREATED)
def create_warning(
    payload: WarningCreate,
    _operator: object = Depends(require_operator),
    repo: OfficialWarningRepository = Depends(get_warning_repository),
) -> OfficialWarningContract:
    """Ingest or curate an official warning. Restricted to operator/admin roles."""
    model = repo.save(payload)
    return repo.to_contract(model)


@router.post(
    "/import-fixtures",
    response_model=list[OfficialWarningContract],
    status_code=status.HTTP_201_CREATED,
)
def import_fixtures(
    _operator: object = Depends(require_operator),
    db: Session = Depends(_get_db),
    repo: OfficialWarningRepository = Depends(get_warning_repository),
) -> list[OfficialWarningContract]:
    """Import clearly labelled sample warning fixtures. Restricted to operator/admin roles."""
    models = import_sample_fixtures(db)
    return [repo.to_contract(m) for m in models]
