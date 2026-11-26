"""Contracts for scheduled ingestion runs, retries, and monitoring."""

from enum import StrEnum

from pydantic import BaseModel

from app.schemas.common import AwareDatetime


class IngestionRunStatus(StrEnum):
    """Lifecycle status of an ingestion run."""

    RUNNING = "running"
    SUCCESS = "success"
    RETRYING = "retrying"
    FAILED = "failed"


class IngestionRunRecord(BaseModel):
    """Persisted ingestion run record with retry and count metrics."""

    run_id: str
    source_id: str
    trigger_mode: str
    status: IngestionRunStatus
    attempts: int
    max_attempts: int
    records_ingested: int = 0
    records_skipped: int = 0
    error_message: str | None = None
    started_at: AwareDatetime
    finished_at: AwareDatetime | None = None
    next_retry_at: AwareDatetime | None = None


class IngestionRunListResponse(BaseModel):
    """Response envelope for listing ingestion runs."""

    total: int
    items: list[IngestionRunRecord]


class IngestionHealthSummary(BaseModel):
    """Operational monitoring summary for scheduled ingestion and source freshness."""

    scheduler_enabled: bool
    poll_interval_seconds: int
    total_sources: int
    fresh_sources: int
    stale_sources: int
    unknown_sources: int
    recent_success_runs: int
    recent_failed_runs: int
    active_retrying_runs: int
    last_run_at: AwareDatetime | None = None
