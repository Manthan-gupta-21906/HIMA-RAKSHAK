"""Repository for observation persistence with idempotent batch upsert."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion.column_mapping import compute_idempotency_key
from app.models.observation import ObservationModel
from app.schemas.observation import ObservationContract


class ObservationRepository:
    """SQLAlchemy-backed repository for environmental observations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert_batch(self, contracts: list[ObservationContract]) -> tuple[int, int]:
        """Insert observations idempotently; returns (inserted, skipped_duplicates)."""
        if not contracts:
            return 0, 0

        keys = [
            compute_idempotency_key(
                c.location_id, c.source_id, c.observed_at, c.metric.value
            )
            for c in contracts
        ]
        existing_keys = set(
            self._db.scalars(
                select(ObservationModel.idempotency_key).where(
                    ObservationModel.idempotency_key.in_(keys)
                )
            ).all()
        )

        inserted = 0
        skipped = 0
        seen_in_batch: set[str] = set()
        now = datetime.now(UTC)

        for contract, key in zip(contracts, keys, strict=True):
            if key in existing_keys or key in seen_in_batch:
                skipped += 1
                continue
            seen_in_batch.add(key)
            self._db.add(
                ObservationModel(
                    observation_id=contract.observation_id,
                    location_id=contract.location_id,
                    source_id=contract.source_id,
                    observed_at=contract.observed_at,
                    metric=contract.metric.value,
                    value=contract.value,
                    unit=contract.unit,
                    idempotency_key=key,
                    is_demo_fixture=contract.is_demo_fixture,
                    ingested_at=now,
                )
            )
            inserted += 1

        self._db.flush()
        return inserted, skipped

    def list_by_location(
        self, location_id: str, metric: str | None = None
    ) -> list[ObservationModel]:
        """List observations for a location, optionally filtered by metric."""
        stmt = select(ObservationModel).where(
            ObservationModel.location_id == location_id
        )
        if metric:
            stmt = stmt.where(ObservationModel.metric == metric)
        stmt = stmt.order_by(ObservationModel.observed_at.desc())
        return list(self._db.scalars(stmt).all())

    def count(self) -> int:
        """Return total persisted observations."""
        return int(
            self._db.scalar(select(func.count()).select_from(ObservationModel)) or 0
        )

    def save(self, model: ObservationModel) -> ObservationModel:
        """Persist a new observation model and flush to get the DB-generated state."""
        self._db.add(model)
        self._db.flush()
        return model

    def get_by_idempotency_key(self, key: str) -> ObservationModel | None:
        """Return an existing observation with the given idempotency key, or None."""
        return self._db.scalar(
            select(ObservationModel).where(ObservationModel.idempotency_key == key)
        )

    def get_by_id(self, observation_id: str) -> ObservationModel | None:
        """Return an observation by its primary key, or None."""
        return self._db.get(ObservationModel, observation_id)
