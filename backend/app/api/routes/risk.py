"""Risk assessment API routes — current state, history, and spatial summary."""

from collections.abc import Generator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_any_authenticated, require_operator
from app.db.session import get_db
from app.models.alert import AlertActionModel  # noqa: F401
from app.models.location import LocationModel  # noqa: F401
from app.models.observation import ObservationModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel  # noqa: F401
from app.repositories.location_repository import SqlAlchemyLocationRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.common import HazardType, PaginationMeta
from app.schemas.exposure import LocationExposureProfile, PriorityAssessment
from app.schemas.risk import (
    LocationRiskState,
    ReplayEventsResponse,
    RiskAssessmentContract,
    RiskAssessmentRequest,
    RiskHistoryResponse,
)
from app.services.location_service import LocationNotFoundError
from app.services.risk_service import RiskService
from app.services.risk_workflow import RiskEvaluationResponse, RiskWorkflowService

router = APIRouter(prefix="/risk", tags=["risk"])


def _get_db() -> Generator[Session, None, None]:
    yield from get_db()


def get_risk_service(db: Session = Depends(_get_db)) -> RiskService:
    return RiskService(
        risk_repo=RiskAssessmentRepository(db),
        observation_repo=ObservationRepository(db),
        location_repo=SqlAlchemyLocationRepository(db),
        source_repo=SourceRepository(db),
    )


def get_risk_workflow_service(db: Session = Depends(_get_db)) -> RiskWorkflowService:
    return RiskWorkflowService(db)


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


def _run_evaluate_location_risk(
    location_id: str,
    trigger_alert: bool,
    workflow: RiskWorkflowService,
    cutoff_at: datetime | None = None,
) -> RiskEvaluationResponse:
    """Shared implementation for /evaluate and /assess endpoints."""
    try:
        return workflow.evaluate_location(
            location_id,
            trigger_alert=trigger_alert,
            cutoff_at=cutoff_at,
        )
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/evaluate/{location_id}",
    response_model=RiskEvaluationResponse,
    summary="Evaluate hazard risk, exposure, priority, and alerts from observations",
)
def evaluate_location_risk(
    location_id: str,
    payload: RiskAssessmentRequest | None = None,
    trigger_alert: bool = Query(
        default=True,
        description="Whether to persist an operational alert if priority warrants action",
    ),
    _user: object = Depends(require_operator),
    workflow: RiskWorkflowService = Depends(get_risk_workflow_service),
) -> RiskEvaluationResponse:
    """Controlled assessment workflow extracting features from persisted observations."""
    return _run_evaluate_location_risk(
        location_id,
        trigger_alert,
        workflow,
        cutoff_at=payload.cutoff_at if payload else None,
    )


@router.post(
    "/assess/{location_id}",
    response_model=RiskEvaluationResponse,
    summary="Assess hazard risk, exposure, priority, and alerts from observations",
)
def assess_location_risk(
    location_id: str,
    payload: RiskAssessmentRequest | None = None,
    trigger_alert: bool = Query(
        default=True,
        description="Whether to persist an operational alert if priority warrants action",
    ),
    _user: object = Depends(require_operator),
    workflow: RiskWorkflowService = Depends(get_risk_workflow_service),
) -> RiskEvaluationResponse:
    """Alias for /evaluate: same controlled assessment workflow via /risk/assess."""
    return _run_evaluate_location_risk(
        location_id,
        trigger_alert,
        workflow,
        cutoff_at=payload.cutoff_at if payload else None,
    )


@router.get(
    "/exposure/{location_id}",
    response_model=LocationExposureProfile,
    summary="Spatial exposure profile for a location",
)
def get_location_exposure(
    location_id: str,
    _user: object = Depends(require_any_authenticated),
    workflow: RiskWorkflowService = Depends(get_risk_workflow_service),
) -> LocationExposureProfile:
    """Calculate affected population, infrastructure, and critical assets from geospatial layers."""
    try:
        return workflow.get_exposure(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/priority/{location_id}",
    response_model=PriorityAssessment,
    summary="Explainable risk priority assessment for a location",
)
def get_location_priority(
    location_id: str,
    _user: object = Depends(require_any_authenticated),
    workflow: RiskWorkflowService = Depends(get_risk_workflow_service),
) -> PriorityAssessment:
    """Generate explainable priority record from hazard, exposure, confidence, and readiness."""
    try:
        return workflow.get_priority(location_id)
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/replay",
    response_model=ReplayEventsResponse,
    summary="Persisted historical replay sequences",
)
def get_replay_events(
    location_id: str | None = Query(default=None, description="Optional location ID filter"),
    hazard_type: HazardType | None = Query(
        default=None, description="Optional hazard type filter (flood or avalanche)"
    ),
    since: datetime | None = Query(
        default=None, description="Include assessments on or after this timestamp (ISO 8601)"
    ),
    limit: int = Query(
        default=50, ge=1, le=200, description="Max frames per location/hazard sequence"
    ),
    _user: object = Depends(require_any_authenticated),
    service: RiskService = Depends(get_risk_service),
) -> ReplayEventsResponse:
    """Return chronological historical replay sequences reconstructed from
    persisted risk assessment history. Hazard pathways remain distinct."""
    try:
        return service.get_replay_events(
            location_id=location_id,
            hazard_type=hazard_type,
            since=since,
            limit=limit,
        )
    except LocationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
