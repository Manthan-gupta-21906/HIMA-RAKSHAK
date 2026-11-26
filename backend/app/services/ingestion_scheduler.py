"""Scheduled ingestion runner, retry orchestration, and source health monitoring."""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib import request as urllib_request
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.models.source import SourceModel
from app.repositories.ingestion_run_repository import IngestionRunRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.common import FreshnessStatus
from app.schemas.ingestion import (
    IngestionHealthSummary,
    IngestionRunRecord,
    IngestionRunStatus,
)
from app.schemas.source import compute_freshness
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SAMPLE_CSV = REPO_ROOT / "data" / "fixtures" / "sample_observations.csv"


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


class IngestionScheduler:
    """Executes scheduled and manual source ingestion with retries and monitoring."""

    def __init__(
        self,
        session_factory: sessionmaker[Session] | None = None,
        settings: Settings | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings or get_settings()
        self._sleep = sleep_fn or time.sleep
        self._task: asyncio.Task[None] | None = None
        self._stop_event: asyncio.Event | None = None

    @staticmethod
    def is_source_due(source: SourceModel, now: datetime | None = None) -> bool:
        """Return True if a source has never been fetched or exceeded its update cadence."""
        current = now or datetime.now(UTC)
        last = _ensure_utc(source.last_fetched_at)
        if last is None:
            return True
        cadence = timedelta(minutes=max(1, source.update_frequency_minutes))
        return (current - last) >= cadence

    @staticmethod
    def _default_fetch_csv(source: SourceModel) -> str | Path:
        """Resolve CSV payload or fixture path for a source."""
        url = (source.reference_url or "").strip()
        if source.access_mode == "live" and url.startswith(("http://", "https://")) and url.endswith(".csv"):
            with urllib_request.urlopen(url, timeout=10.0) as resp:
                return resp.read().decode("utf-8")
        if DEFAULT_SAMPLE_CSV.exists():
            return DEFAULT_SAMPLE_CSV
        raise FileNotFoundError(
            f"No live CSV endpoint or local fixture available for source '{source.source_id}'."
        )

    def ingest_source_with_retries(
        self,
        db: Session,
        source_id: str,
        *,
        trigger_mode: str = "manual",
        fetcher: Callable[[SourceModel], str | Path] | None = None,
        max_attempts: int | None = None,
        backoff_seconds: float | None = None,
    ) -> IngestionRunRecord:
        """Run ingestion for a source with exponential backoff retries and run tracking."""
        source_repo = SourceRepository(db)
        obs_repo = ObservationRepository(db)
        run_repo = IngestionRunRepository(db)
        ingestion_service = IngestionService(obs_repo=obs_repo, source_repo=source_repo)

        source = source_repo.get_by_id(source_id)
        attempts_limit = max(1, max_attempts or self._settings.ingestion_max_retries)
        base_backoff = (
            self._settings.ingestion_retry_backoff_seconds
            if backoff_seconds is None
            else backoff_seconds
        )
        resolve_csv = fetcher or self._default_fetch_csv

        run_id = f"ing-{uuid4().hex[:12]}"
        started_at = datetime.now(UTC)
        record = IngestionRunRecord(
            run_id=run_id,
            source_id=source_id,
            trigger_mode=trigger_mode,
            status=IngestionRunStatus.RUNNING,
            attempts=0,
            max_attempts=attempts_limit,
            started_at=started_at,
        )
        run_repo.create_or_update(record)

        last_error: str | None = None
        for attempt in range(1, attempts_limit + 1):
            record.attempts = attempt
            try:
                csv_payload = resolve_csv(source)
                summary = ingestion_service.ingest_csv(
                    csv_source=csv_payload,
                    source_id=source_id,
                )
                source.last_fetched_at = datetime.now(UTC)
                source_repo.upsert(source)

                record.status = IngestionRunStatus.SUCCESS
                record.records_ingested = summary.inserted
                record.records_skipped = summary.skipped_duplicates
                record.error_message = None
                record.next_retry_at = None
                record.finished_at = datetime.now(UTC)
                return run_repo.create_or_update(record)
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Ingestion attempt %d/%d failed for source %s: %s",
                    attempt,
                    attempts_limit,
                    source_id,
                    last_error,
                )
                if attempt < attempts_limit:
                    delay = base_backoff * (2 ** (attempt - 1))
                    record.status = IngestionRunStatus.RETRYING
                    record.error_message = last_error
                    record.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)
                    run_repo.create_or_update(record)
                    if delay > 0:
                        self._sleep(delay)

        record.status = IngestionRunStatus.FAILED
        record.error_message = last_error
        record.next_retry_at = None
        record.finished_at = datetime.now(UTC)
        return run_repo.create_or_update(record)

    def run_due_sources(
        self,
        db: Session,
        *,
        now: datetime | None = None,
        fetcher: Callable[[SourceModel], str | Path] | None = None,
    ) -> list[IngestionRunRecord]:
        """Inspect all sources and ingest any that are due according to their cadence."""
        source_repo = SourceRepository(db)
        current = now or datetime.now(UTC)
        results: list[IngestionRunRecord] = []
        for source in source_repo.list_all():
            if self.is_source_due(source, current):
                run = self.ingest_source_with_retries(
                    db,
                    source.source_id,
                    trigger_mode="scheduled",
                    fetcher=fetcher,
                )
                results.append(run)
        return results

    @staticmethod
    def get_monitoring_summary(
        db: Session, settings: Settings | None = None
    ) -> IngestionHealthSummary:
        """Compute source freshness and recent ingestion run health metrics."""
        cfg = settings or get_settings()
        source_repo = SourceRepository(db)
        run_repo = IngestionRunRepository(db)

        sources = source_repo.list_all()
        fresh = 0
        stale = 0
        unknown = 0
        for s in sources:
            f = compute_freshness(
                s.update_frequency_minutes, _ensure_utc(s.last_fetched_at)
            )
            if f == FreshnessStatus.FRESH:
                fresh += 1
            elif f == FreshnessStatus.STALE:
                stale += 1
            else:
                unknown += 1

        recent_runs = run_repo.list_runs(limit=100)
        success_runs = sum(1 for r in recent_runs if r.status == IngestionRunStatus.SUCCESS)
        failed_runs = sum(1 for r in recent_runs if r.status == IngestionRunStatus.FAILED)
        retrying_runs = sum(1 for r in recent_runs if r.status == IngestionRunStatus.RETRYING)
        last_run_at = recent_runs[0].started_at if recent_runs else None

        return IngestionHealthSummary(
            scheduler_enabled=cfg.ingestion_scheduler_enabled,
            poll_interval_seconds=cfg.ingestion_poll_interval_seconds,
            total_sources=len(sources),
            fresh_sources=fresh,
            stale_sources=stale,
            unknown_sources=unknown,
            recent_success_runs=success_runs,
            recent_failed_runs=failed_runs,
            active_retrying_runs=retrying_runs,
            last_run_at=last_run_at,
        )

    async def _loop(self) -> None:
        assert self._stop_event is not None
        interval = max(5, self._settings.ingestion_poll_interval_seconds)
        while not self._stop_event.is_set():
            if self._session_factory is not None:
                db = self._session_factory()
                try:
                    await asyncio.to_thread(self.run_due_sources, db)
                except Exception:
                    logger.exception("Scheduled ingestion cycle failed.")
                finally:
                    db.close()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except TimeoutError:
                continue

    def start(self) -> None:
        """Start the background scheduled ingestion loop if enabled."""
        if not self._settings.ingestion_scheduler_enabled or self._task is not None:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._loop())
        logger.info(
            "Started IngestionScheduler (interval=%ss)",
            self._settings.ingestion_poll_interval_seconds,
        )

    async def stop(self) -> None:
        """Gracefully stop the background scheduled ingestion loop."""
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task is not None:
            try:
                await self._task
            except Exception:
                pass
            self._task = None
