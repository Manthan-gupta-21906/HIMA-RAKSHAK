"""System-generated operational alerts and action history routes.

Authoritative CWC/DGRE/IMD bulletins remain isolated under /warnings.
"""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_any_authenticated, require_operator
from app.db.session import get_db
from app.models.alert import AlertActionModel  # noqa: F401
from app.models.user import UserModel
from app.repositories.alert_repository import AlertRepository
from app.schemas.alert import (
    AcknowledgeAlertRequest,
    AlertActionRecord,
    AlertDeliveryListResponse,
    AlertListResponse,
    AlertStatus,
    DeliverAlertRequest,
    UpdateAlertActionRequest,
)
from app.schemas.common import HazardType
from app.services.alert_service import AlertNotFoundError, AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _get_db() -> Generator[Session, None, None]:
    yield from get_db()


def get_alert_service(db: Session = Depends(_get_db)) -> AlertService:
    return AlertService(AlertRepository(db))


@router.get("", response_model=AlertListResponse, summary="List system-generated alerts")
def list_alerts(
    location_id: str | None = Query(default=None, description="Filter by location ID"),
    alert_status: AlertStatus | None = Query(
        default=None, alias="status", description="Filter by alert status"
    ),
    hazard_type: HazardType | None = Query(default=None, description="Filter by hazard type"),
    _user: object = Depends(require_any_authenticated),
    service: AlertService = Depends(get_alert_service),
) -> AlertListResponse:
    """List persisted operational alerts (distinct from authoritative /warnings)."""
    items = service.list_alerts(
        location_id=location_id,
        status=alert_status,
        hazard_type=hazard_type,
    )
    return AlertListResponse(total=len(items), items=items)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertActionRecord,
    summary="Acknowledge an operational alert",
)
def acknowledge_alert(
    alert_id: str,
    payload: AcknowledgeAlertRequest | None = None,
    user: UserModel = Depends(require_operator),
    service: AlertService = Depends(get_alert_service),
) -> AlertActionRecord:
    """Acknowledge a system alert and record the operator identity."""
    try:
        return service.acknowledge_alert(
            alert_id=alert_id,
            actor_username=user.username,
            note=payload.note if payload else None,
        )
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{alert_id}/action",
    response_model=AlertActionRecord,
    summary="Update action status on an alert",
)
def update_alert_action(
    alert_id: str,
    payload: UpdateAlertActionRequest,
    _user: UserModel = Depends(require_operator),
    service: AlertService = Depends(get_alert_service),
) -> AlertActionRecord:
    """Update operator action status and notes for a system alert."""
    try:
        return service.update_action_status(
            alert_id=alert_id,
            status=payload.status,
            action_note=payload.action_note,
        )
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/{alert_id}/deliver",
    response_model=AlertActionRecord,
    summary="Deliver or retry delivery for an operational alert",
)
def deliver_alert(
    alert_id: str,
    payload: DeliverAlertRequest | None = None,
    _user: UserModel = Depends(require_operator),
    service: AlertService = Depends(get_alert_service),
) -> AlertActionRecord:
    """Trigger or retry operational alert delivery across configured channels."""
    try:
        return service.deliver_alert(
            alert_id=alert_id,
            channels=payload.channels if payload else None,
            webhook_url=payload.webhook_url if payload else None,
            email_recipients=payload.email_recipients if payload else None,
        )
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{alert_id}/deliveries",
    response_model=AlertDeliveryListResponse,
    summary="List delivery attempts and status for an alert",
)
def list_alert_deliveries(
    alert_id: str,
    _user: object = Depends(require_any_authenticated),
    service: AlertService = Depends(get_alert_service),
) -> AlertDeliveryListResponse:
    """Inspect delivery attempts, HTTP response codes, errors, and overall delivery status."""
    try:
        overall_status, items = service.list_deliveries(alert_id)
        return AlertDeliveryListResponse(
            alert_id=alert_id,
            delivery_status=overall_status,
            total=len(items),
            items=items,
        )
    except AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
