"""Authoritative read-only official warning contracts."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import AwareDatetime, HazardType, PaginationMeta


class WarningAuthority(StrEnum):
    """Official agencies issuing authoritative warnings."""

    CWC = "CWC"
    IMD = "IMD"
    DGRE = "DGRE"
    SDMA = "SDMA"


class OfficialWarningContract(BaseModel):
    """Read-only official warning record preserving authority and validity."""

    warning_id: str = Field(..., min_length=2, max_length=64)
    authority: WarningAuthority
    hazard_type: HazardType
    location_id: str = Field(..., min_length=3, max_length=32)
    severity_label: str = Field(..., min_length=2, max_length=64)
    headline: str = Field(..., min_length=4, max_length=240)
    issued_at: AwareDatetime
    valid_until: AwareDatetime
    is_read_only: Literal[True] = True
    provenance: str = Field(..., min_length=2, max_length=160)
    geographic_scope: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=1000)
    advisory_notes: str | None = Field(default=None, max_length=1000)
    source_url: str | None = Field(default=None, max_length=500)
    source_reference: str | None = Field(default=None, max_length=200)
    is_demo_fixture: bool = True
    is_expired: bool = False

    @model_validator(mode="after")
    def validate_validity_window(self) -> "OfficialWarningContract":
        if self.valid_until <= self.issued_at:
            raise ValueError("valid_until must be strictly after issued_at.")
        now = datetime.now(UTC)
        if now >= self.valid_until:
            self.is_expired = True
        return self


class WarningCreate(BaseModel):
    """Payload to curate or ingest an official warning."""

    warning_id: str = Field(..., min_length=2, max_length=64)
    authority: WarningAuthority
    hazard_type: HazardType
    location_id: str = Field(..., min_length=3, max_length=32)
    severity_label: str = Field(..., min_length=2, max_length=64)
    headline: str = Field(..., min_length=4, max_length=240)
    issued_at: AwareDatetime
    valid_until: AwareDatetime
    geographic_scope: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=1000)
    advisory_notes: str | None = Field(default=None, max_length=1000)
    source_url: str | None = Field(default=None, max_length=500)
    source_reference: str | None = Field(default=None, max_length=200)
    provenance: str = Field(..., min_length=2, max_length=160)
    is_demo_fixture: bool = False

    @model_validator(mode="after")
    def validate_validity(self) -> "WarningCreate":
        if self.valid_until <= self.issued_at:
            raise ValueError("valid_until must be strictly after issued_at.")
        return self


class WarningListResponse(BaseModel):
    """Paginated collection of official warnings."""

    total: int
    items: list[OfficialWarningContract]
    pagination: PaginationMeta
