"""Service layer for environmental observations."""

import uuid
from datetime import UTC, datetime

from app.ingestion.column_mapping import compute_idempotency_key
from app.models.observation import ObservationModel
from app.models.source import SourceModel
from app.repositories.observation_repository import ObservationRepository
from app.schemas.observation import ObservationContract, ObservationCreate, ObservationMetric


class LocationNotFoundError(Exception):
    """Raised when the referenced location does not exist in the database."""


class IncompatibleHazardError(Exception):
    """Raised when the location does not support the requested hazard type."""


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
    """Service layer for querying and creating environmental observations."""

    def __init__(self, repo: ObservationRepository) -> None:
        self._repo = repo

    def create_observation(self, payload: ObservationCreate) -> ObservationContract:
        """
        Persist a field or telemetry observation after validating location and hazard.

        Raises:
            LocationNotFoundError: If location_id does not exist.
            IncompatibleHazardError: If the location does not support the hazard_type.
        """

        from app.models.location import LocationModel

        db = self._repo._db  # type: ignore[attr-defined]

        # 1. Verify location exists
        location = db.get(LocationModel, payload.location_id)
        if location is None:
            raise LocationNotFoundError(payload.location_id)

        # 2. Check hazard compatibility against location's supported_hazards
        if payload.hazard_type is not None:
            supported = [h.lower() for h in (location.supported_hazards or [])]
            if payload.hazard_type.value not in supported:
                raise IncompatibleHazardError(
                    f"Location '{payload.location_id}' does not support hazard "
                    f"'{payload.hazard_type.value}'. Supported: {location.supported_hazards}"
                )

        # 3. Ensure the default field-observation source record exists
        source_id = payload.source_id or "src-field-obs"
        src = db.get(SourceModel, source_id)
        if src is None:
            src = SourceModel(
                source_id=source_id,
                source_name="Field Observation",
                provider="HIMA-RAKSHAK Field Unit",
                dataset="field_observation",
                source_type="field_observation",
                access_mode="manual",
                licence="Internal Use Only",
                reference_url="",
                update_frequency_minutes=0,
                trust_classification="field",
                is_authoritative=False,
                is_demo_fixture=False,
            )
            db.add(src)
            db.flush()

        # 4. Compute idempotency key and check for duplicates
        observed_at = payload.observed_at or datetime.now(UTC)
        idem_key = compute_idempotency_key(
            payload.location_id, source_id, observed_at, payload.metric.value  # type: ignore[union-attr]
        )
        existing = self._repo.get_by_idempotency_key(idem_key)
        if existing is not None:
            return model_to_contract(existing)

        # 5. Persist and return
        model = ObservationModel(
            observation_id=str(uuid.uuid4()),
            location_id=payload.location_id,
            source_id=source_id,
            observed_at=observed_at,
            metric=payload.metric.value,  # type: ignore[union-attr]
            value=payload.value,
            unit=payload.unit,
            idempotency_key=idem_key,
            is_demo_fixture=False,
            ingested_at=datetime.now(UTC),
        )
        saved = self._repo.save(model)
        return model_to_contract(saved)

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
