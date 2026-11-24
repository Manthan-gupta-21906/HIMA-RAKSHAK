"""Repository for source registry records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import SourceModel


class SourceNotFoundError(Exception):
    """Raised when a requested source_id does not exist."""


class SourceRepository:
    """SQLAlchemy-backed repository for data source metadata."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, source_id: str) -> SourceModel:
        row = self._db.get(SourceModel, source_id)
        if row is None:
            raise SourceNotFoundError(f"Source '{source_id}' not found.")
        return row

    def list_all(
        self,
        source_type: str | None = None,
        access_mode: str | None = None,
    ) -> list[SourceModel]:
        stmt = select(SourceModel)
        if source_type:
            stmt = stmt.where(SourceModel.source_type == source_type)
        if access_mode:
            stmt = stmt.where(SourceModel.access_mode == access_mode)
        return list(self._db.scalars(stmt).all())

    def upsert(self, model: SourceModel) -> SourceModel:
        self._db.merge(model)
        self._db.flush()
        return self._db.get(SourceModel, model.source_id)  # type: ignore[return-value]

    def count(self) -> int:
        from sqlalchemy import func

        return int(
            self._db.scalar(select(func.count()).select_from(SourceModel)) or 0
        )
