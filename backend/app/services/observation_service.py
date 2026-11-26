"""Service layer for environmental observations."""

from datetime import UTC, datetime

from app.models.observation import ObservationModel
from app.repositories.observation_repository import ObservationRepository
from app.schemas.observation import ObservationContract, ObservationMetric


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def model_to_contract(m: ObservationModel) -> ObservationContract:
    """Convert an ObservationModel ORM instance to an ObservationContract."""
    return ObservationContract(
        observation_id=m.observation_id,
        location_id=m.location_id,
        source_id=m.source_id,
        observed_at=_ensure_utc(m.observed_at),
        metric=ObservationMetric(m.metric),
        value=m.value,
        unit=m.unit,
        is_demo_fixture=m.is_demo_fixture,
    )


class ObservationService:
    """Service layer for querying environmental observations."""

    def __init__(self, repo: ObservationRepository) -> None:
        self._repo = repo

    def list_observations(
        self,
        location_id: str,
        metric: ObservationMetric | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ObservationContract], int]:
        """List observations filtered by location, metric, and date range."""
        models = self._repo.list_by_location(
            location_id=location_id,
            metric=metric.value if metric else None,
        )

        if since is not None:
            since_cmp = since.replace(tzinfo=None) if since.tzinfo else since
            models = [
                m
                for m in models
                if (m.observed_at.replace(tzinfo=None) if m.observed_at.tzinfo else m.observed_at)
                >= since_cmp
            ]
        if until is not None:
            until_cmp = until.replace(tzinfo=None) if until.tzinfo else until
            models = [
                m
                for m in models
                if (m.observed_at.replace(tzinfo=None) if m.observed_at.tzinfo else m.observed_at)
                <= until_cmp
            ]

        total = len(models)
        start_idx = (page - 1) * page_size
        page_models = models[start_idx : start_idx + page_size]
        items = [model_to_contract(m) for m in page_models]
        return items, total
