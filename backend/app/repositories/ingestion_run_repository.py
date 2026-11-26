"""Repository for persisting and querying ingestion run monitoring records."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ingestion_run import IngestionRunModel
from app.schemas.ingestion import IngestionRunRecord, IngestionRunStatus


class IngestionRunRepository:
    """SQLAlchemy-backed repository for ingestion runs."""

    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def _ensure_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    @classmethod
    def _to_contract(cls, row: IngestionRunModel) -> IngestionRunRecord:
        return IngestionRunRecord(
            run_id=row.run_id,
            source_id=row.source_id,
            trigger_mode=row.trigger_mode,
            status=IngestionRunStatus(row.status),
            attempts=row.attempts,
            max_attempts=row.max_attempts,
            records_ingested=row.records_ingested,
            records_skipped=row.records_skipped,
            error_message=row.error_message,
            started_at=cls._ensure_utc(row.started_at) or datetime.now(UTC),
            finished_at=cls._ensure_utc(row.finished_at),
            next_retry_at=cls._ensure_utc(row.next_retry_at),
        )

    def create_or_update(self, record: IngestionRunRecord) -> IngestionRunRecord:
        """Persist or update an ingestion run record."""
        existing = self._db.get(IngestionRunModel, record.run_id)
        if existing is not None:
            existing.status = record.status.value
            existing.attempts = record.attempts
            existing.max_attempts = record.max_attempts
            existing.records_ingested = record.records_ingested
            existing.records_skipped = record.records_skipped
            existing.error_message = record.error_message
            existing.finished_at = record.finished_at
            existing.next_retry_at = record.next_retry_at
            self._db.commit()
            self._db.refresh(existing)
            return self._to_contract(existing)

        row = IngestionRunModel(
            run_id=record.run_id,
            source_id=record.source_id,
            trigger_mode=record.trigger_mode,
            status=record.status.value,
            attempts=record.attempts,
            max_attempts=record.max_attempts,
            records_ingested=record.records_ingested,
            records_skipped=record.records_skipped,
            error_message=record.error_message,
            started_at=record.started_at,
            finished_at=record.finished_at,
            next_retry_at=record.next_retry_at,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return self._to_contract(row)

    def list_runs(
        self,
        *,
        source_id: str | None = None,
        status: IngestionRunStatus | None = None,
        limit: int = 50,
    ) -> list[IngestionRunRecord]:
        """List ingestion runs ordered newest-first."""
        stmt = select(IngestionRunModel)
        if source_id:
            stmt = stmt.where(IngestionRunModel.source_id == source_id)
        if status:
            stmt = stmt.where(IngestionRunModel.status == status.value)
        stmt = stmt.order_by(IngestionRunModel.started_at.desc()).limit(limit)
        rows = self._db.scalars(stmt).all()
        return [self._to_contract(r) for r in rows]
