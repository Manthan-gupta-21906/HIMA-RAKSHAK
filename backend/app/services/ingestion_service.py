"""Service layer for CSV observation ingestion with source verification."""

from pathlib import Path

from pydantic import BaseModel

from app.ingestion.column_mapping import ColumnMapping
from app.ingestion.csv_loader import CsvRowError, load_observations_from_csv
from app.repositories.observation_repository import ObservationRepository
from app.repositories.source_repository import SourceRepository


class ImportSummary(BaseModel):
    """Structured summary returned after a CSV ingestion run."""

    source_id: str
    total_rows: int
    valid_rows: int
    inserted: int
    skipped_duplicates: int
    error_count: int
    errors: list[CsvRowError]


class IngestionService:
    """Coordinates source verification, CSV parsing, and idempotent batch persistence."""

    def __init__(
        self,
        obs_repo: ObservationRepository,
        source_repo: SourceRepository,
    ) -> None:
        self._obs_repo = obs_repo
        self._source_repo = source_repo

    def ingest_csv(
        self,
        csv_source: str | Path,
        source_id: str,
        mapping: ColumnMapping | None = None,
        is_demo_fixture: bool | None = None,
    ) -> ImportSummary:
        """Validate source existence, parse CSV rows, and persist valid observations."""
        source = self._source_repo.get_by_id(source_id)
        demo_flag = source.is_demo_fixture if is_demo_fixture is None else is_demo_fixture

        parsed = load_observations_from_csv(
            csv_source=csv_source,
            source_id=source_id,
            mapping=mapping,
            is_demo_fixture=demo_flag,
        )
        inserted, skipped = self._obs_repo.upsert_batch(parsed.valid)
        return ImportSummary(
            source_id=source_id,
            total_rows=parsed.total_rows,
            valid_rows=len(parsed.valid),
            inserted=inserted,
            skipped_duplicates=skipped,
            error_count=len(parsed.errors),
            errors=parsed.errors,
        )
