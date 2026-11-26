"""Risk assessment API routes — current state, history, and spatial summary."""

from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_any_authenticated
from app.db.session import get_db
from app.models.location import LocationModel  # noqa: F401
from app.models.observation import ObservationModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel  # noqa: F401
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import HazardType, PaginationMeta
from app.schemas.risk import (
    LocationRiskState,
    RiskAssessmentContract,
    RiskHistoryResponse,
)
from app.services.location_service import LocationNotFoundError
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["risk"])


def _get_db() -> Generator[Session, None, None]:
    yield from get_db()


def get_risk_service(db: Session = Depends(_get_db)) -> RiskService:
    return RiskService(RiskAssessmentRepository(db))


@router.get(
    "/current/{location_id}",
    response_model=dict[str, RiskAssessmentContract | None],
    summary="Latest assessment per hazard type",
)
def get_current_risk(
    location_id: str,
    _user: object = Depends(require_any_authenticated),
    service: RiskService = Depends(get_risk_service),
) -> dict[str, RiskAssessmentContract | None]:
    """Return the latest persisted assessment for each hazard type at a location.

    Keys are hazard type strings (`flood`, `avalanche`). Value is `null` when
    no assessment has been recorded for that hazard.
    """
    return service.get_current_risk(location_id)


@router.get(
    "/history/{location_id}",
    response_model=RiskHistoryResponse,
    summary="Paginated history of risk assessments",
)
def get_risk_history(
    location_id: str,
    hazard_type: HazardType | None = Query(
        default=None, description="Filter by hazard type (flood or avalanche)"
    ),
    since: datetime | None = Query(
        default=None, description="Include only assessments on or after this timestamp (ISO 8601)"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
    _user: object = Depends(require_any_authenticated),
    service: RiskService = Depends(get_risk_service),
) -> RiskHistoryResponse:
    """List historical risk assessments for a location with pagination and filters."""
    items, total, has_next = service.get_risk_history(
        location_id=location_id,
        hazard_type=hazard_type,
        since=since,
        page=page,
        page_size=page_size,
    )
    return RiskHistoryResponse(
        total=total,
        items=items,
        pagination=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        ),
    )


@router.get(
    "/state/{location_id}",
    response_model=LocationRiskState,
    summary="Unified multi-hazard spatial state",
)
def get_risk_state(
    location_id: str,
    _user: object = Depends(require_any_authenticated),
    service: RiskService = Depends(get_risk_service),
) -> LocationRiskState:
    """Return the co-located multi-hazard spatial state keeping hazard outputs distinct."""
    try:
        return service.get_location_risk_state(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
