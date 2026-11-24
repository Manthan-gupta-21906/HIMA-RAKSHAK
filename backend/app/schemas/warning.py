"""Authoritative read-only official warning contracts."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import AwareDatetime, HazardType


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

    @model_validator(mode="after")
    def validate_validity_window(self) -> "OfficialWarningContract":
        if self.valid_until <= self.issued_at:
            raise ValueError("valid_until must be strictly after issued_at.")
        return self
