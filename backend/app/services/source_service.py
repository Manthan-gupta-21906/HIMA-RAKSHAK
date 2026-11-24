"""Business logic for the source registry."""

from datetime import UTC, datetime

from app.models.source import SourceModel
from app.repositories.source_repository import SourceRepository
from app.schemas.source import (
    AccessMode,
    SourceContract,
    SourceResponse,
    SourceType,
    TrustClassification,
    compute_freshness,
)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class SourceService:
    """Service layer for querying and managing data sources."""

    def __init__(self, repo: SourceRepository) -> None:
        self._repo = repo

    def _to_response(self, row: SourceModel) -> SourceResponse:
        created_at = _ensure_utc(row.created_at) or datetime.now(UTC)
        last_fetched_at = _ensure_utc(row.last_fetched_at)
        freshness = compute_freshness(
            row.update_frequency_minutes,
            last_fetched_at,
        )
        return SourceResponse(
            source_id=row.source_id,
            source_name=row.source_name,
            provider=row.provider,
            dataset=row.dataset,
            source_type=SourceType(row.source_type),
            access_mode=AccessMode(row.access_mode),
            licence=row.licence,
            reference_url=row.reference_url,
            update_frequency_minutes=row.update_frequency_minutes,
            trust_classification=TrustClassification(row.trust_classification),
            is_authoritative=row.is_authoritative,
            is_demo_fixture=row.is_demo_fixture,
            freshness=freshness,
            last_fetched_at=last_fetched_at,
            created_at=created_at,
        )

    def list_sources(
        self,
        source_type: str | None = None,
        access_mode: str | None = None,
    ) -> list[SourceResponse]:
        rows = self._repo.list_all(
            source_type=source_type,
            access_mode=access_mode,
        )
        return [self._to_response(r) for r in rows]

    def get_source(self, source_id: str) -> SourceResponse:
        """Retrieve a single source by ID, raising SourceNotFoundError if missing."""
        row = self._repo.get_by_id(source_id)
        return self._to_response(row)

    def register_source(self, payload: SourceContract) -> SourceResponse:
        """Register or update a source entry."""
        provider = payload.provider or payload.source_name or payload.source_id
        dataset = payload.dataset or payload.source_name or payload.source_id
        source_name = payload.source_name or f"{provider} - {dataset}"

        row = SourceModel(
            source_id=payload.source_id,
            source_name=source_name,
            provider=provider,
            dataset=dataset,
            source_type=payload.source_type.value,
            access_mode=payload.access_mode.value,
            licence=payload.licence,
            reference_url=payload.reference_url,
            update_frequency_minutes=payload.update_frequency_minutes,
            trust_classification=payload.trust_classification.value,
            is_authoritative=payload.is_authoritative,
            is_demo_fixture=payload.is_demo_fixture,
            created_at=datetime.now(UTC),
        )
        saved = self._repo.upsert(row)
        return self._to_response(saved)

    def record_fetch(self, source_id: str) -> SourceResponse:
        """Update last_fetched_at to now for a given source."""
        row = self._repo.get_by_id(source_id)
        row.last_fetched_at = datetime.now(UTC)
        saved = self._repo.upsert(row)
        return self._to_response(saved)
