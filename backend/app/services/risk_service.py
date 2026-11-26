"""Service layer for querying multi-hazard risk assessments."""

from datetime import datetime

from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import HazardType
from app.schemas.risk import LocationRiskState, RiskAssessmentContract
from app.services.location_service import LocationNotFoundError
from app.services.risk_orchestrator import RiskOrchestrator


class RiskService:
    """Service layer for querying current and historical risk assessments."""

    def __init__(self, risk_repo: RiskAssessmentRepository) -> None:
        self._risk_repo = risk_repo
        self._orchestrator = RiskOrchestrator(risk_repo)

    def get_current_risk(
        self, location_id: str
    ) -> dict[str, RiskAssessmentContract | None]:
        """Return latest assessment for each hazard type for a location."""
        return {
            HazardType.FLOOD.value: self._risk_repo.get_latest_for_location_and_hazard(
                location_id, HazardType.FLOOD
            ),
            HazardType.AVALANCHE.value: self._risk_repo.get_latest_for_location_and_hazard(
                location_id, HazardType.AVALANCHE
            ),
        }

    def get_risk_history(
        self,
        location_id: str,
        hazard_type: HazardType | None = None,
        since: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RiskAssessmentContract], int, bool]:
        """List historical assessments with pagination.

        Returns (items, total, has_next).
        """
        fetch_limit = page * page_size + 1
        all_items = self._risk_repo.list_history(
            location_id=location_id,
            hazard_type=hazard_type,
            since=since,
            limit=fetch_limit,
        )
        total_fetched = len(all_items)
        start_idx = (page - 1) * page_size
        page_items = all_items[start_idx : start_idx + page_size]
        has_next = total_fetched > page * page_size
        total = total_fetched if not has_next else total_fetched - 1
        return page_items, total, has_next

    def get_location_risk_state(self, location_id: str) -> LocationRiskState:
        """Get unified multi-hazard state without blending hazard engines."""
        flood = self._risk_repo.get_latest_for_location_and_hazard(
            location_id, HazardType.FLOOD
        )
        avalanche = self._risk_repo.get_latest_for_location_and_hazard(
            location_id, HazardType.AVALANCHE
        )
        if flood is None and avalanche is None:
            raise LocationNotFoundError(
                f"No risk assessments found for location '{location_id}'."
            )
        return self._orchestrator.get_location_risk_state(location_id)
