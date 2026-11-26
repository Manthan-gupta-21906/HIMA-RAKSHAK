"""Repository for querying and persisting authoritative official warnings."""

from datetime import UTC, datetime
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.official_warning import OfficialWarningModel
from app.schemas.common import HazardType
from app.schemas.warning import (
    OfficialWarningContract,
    WarningAuthority,
    WarningCreate,
)


class OfficialWarningRepository:
    """Encapsulates database access for official authoritative warnings."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, warning_id: str) -> OfficialWarningModel | None:
        """Fetch a single warning record by warning_id."""
        return self.db.get(OfficialWarningModel, warning_id)

    def save(self, warning_data: WarningCreate | OfficialWarningContract) -> OfficialWarningModel:
        """Persist or update an official warning preserving its authority and provenance."""
        now = datetime.now(UTC)
        model = self.get_by_id(warning_data.warning_id)
        if model is None:
            model = OfficialWarningModel(
                warning_id=warning_data.warning_id,
                authority=(
                    warning_data.authority.value
                    if isinstance(warning_data.authority, WarningAuthority)
                    else str(warning_data.authority)
                ),
                hazard_type=(
                    warning_data.hazard_type.value
                    if isinstance(warning_data.hazard_type, HazardType)
                    else str(warning_data.hazard_type)
                ),
                location_id=warning_data.location_id,
                severity_label=warning_data.severity_label,
                headline=warning_data.headline,
                geographic_scope=warning_data.geographic_scope,
                summary=warning_data.summary,
                advisory_notes=warning_data.advisory_notes,
                source_url=warning_data.source_url,
                source_reference=warning_data.source_reference,
                issued_at=warning_data.issued_at,
                valid_until=warning_data.valid_until,
                is_read_only=True,
                provenance=warning_data.provenance,
                is_demo_fixture=warning_data.is_demo_fixture,
                ingested_at=now,
            )
            self.db.add(model)
        else:
            model.authority = (
                warning_data.authority.value
                if isinstance(warning_data.authority, WarningAuthority)
                else str(warning_data.authority)
            )
            model.hazard_type = (
                warning_data.hazard_type.value
                if isinstance(warning_data.hazard_type, HazardType)
                else str(warning_data.hazard_type)
            )
            model.location_id = warning_data.location_id
            model.severity_label = warning_data.severity_label
            model.headline = warning_data.headline
            model.geographic_scope = warning_data.geographic_scope
            model.summary = warning_data.summary
            model.advisory_notes = warning_data.advisory_notes
            model.source_url = warning_data.source_url
            model.source_reference = warning_data.source_reference
            model.issued_at = warning_data.issued_at
            model.valid_until = warning_data.valid_until
            model.provenance = warning_data.provenance
            model.is_demo_fixture = warning_data.is_demo_fixture
            model.ingested_at = now

        self.db.commit()
        self.db.refresh(model)
        return model

    def list_warnings(
        self,
        location_id: str | None = None,
        hazard_type: str | None = None,
        authority: str | None = None,
        is_expired: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[OfficialWarningModel], int]:
        """Query official warnings with optional filters and pagination."""
        query = select(OfficialWarningModel)

        if location_id:
            query = query.where(OfficialWarningModel.location_id == location_id)
        if hazard_type:
            query = query.where(OfficialWarningModel.hazard_type == hazard_type)
        if authority:
            query = query.where(OfficialWarningModel.authority == authority)

        now = datetime.now(UTC)
        if is_expired is True:
            query = query.where(OfficialWarningModel.valid_until <= now)
        elif is_expired is False:
            query = query.where(OfficialWarningModel.valid_until > now)

        count_stmt = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_stmt) or 0

        offset = max(0, (page - 1) * page_size)
        query = query.order_by(OfficialWarningModel.issued_at.desc()).offset(offset).limit(page_size)
        items = list(self.db.scalars(query).all())

        return items, total

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        """Ensure datetimes returned from database carry UTC timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    @classmethod
    def to_contract(cls, model: OfficialWarningModel) -> OfficialWarningContract:
        """Map ORM entity to strongly-typed read-only domain contract."""
        return OfficialWarningContract(
            warning_id=model.warning_id,
            authority=cast(WarningAuthority, WarningAuthority(model.authority)),
            hazard_type=cast(HazardType, HazardType(model.hazard_type)),
            location_id=model.location_id,
            severity_label=model.severity_label,
            headline=model.headline,
            issued_at=cls._ensure_utc(model.issued_at),
            valid_until=cls._ensure_utc(model.valid_until),
            is_read_only=True,
            provenance=model.provenance,
            geographic_scope=model.geographic_scope,
            summary=model.summary,
            advisory_notes=model.advisory_notes,
            source_url=model.source_url,
            source_reference=model.source_reference,
            is_demo_fixture=model.is_demo_fixture,
            is_expired=model.is_expired,
        )
