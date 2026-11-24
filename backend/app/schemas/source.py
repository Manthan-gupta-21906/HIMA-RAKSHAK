"""Source provenance contracts with access mode and freshness."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import AwareDatetime, FreshnessStatus


class SourceType(StrEnum):
    """Classification of environmental or warning data sources."""

    WEATHER = "weather"
    HYDROLOGY = "hydrology"
    SNOW = "snow"
    TERRAIN = "terrain"
    OFFICIAL_WARNING = "official_warning"
    FIELD_OBSERVATION = "field_observation"


class AccessMode(StrEnum):
    """How the system obtains data from this source."""

    LIVE = "live"
    CACHED = "cached"
    SAMPLE = "sample"


class TrustClassification(StrEnum):
    """Trust level assigned to a source."""

    AUTHORITATIVE = "authoritative"
    INSTITUTIONAL = "institutional"
    COMMUNITY = "community"
    DEMO = "demo"


class SourceContract(BaseModel):
    """Full metadata describing an upstream or demo data source."""

    source_id: str = Field(..., min_length=2, max_length=64)
    source_name: str | None = Field(default=None, min_length=2, max_length=120)
    provider: str | None = Field(default=None, min_length=2, max_length=120)
    dataset: str | None = Field(default=None, min_length=2, max_length=120)
    source_type: SourceType
    access_mode: AccessMode = AccessMode.SAMPLE
    licence: str = Field(..., min_length=2, max_length=200)
    reference_url: str = Field(default="", max_length=500)
    update_frequency_minutes: int = Field(..., ge=1, le=10080)
    trust_classification: TrustClassification = TrustClassification.DEMO
    is_authoritative: bool = False
    is_demo_fixture: bool = True

    def model_post_init(self, __context: object) -> None:
        if not self.source_name and not self.provider:
            raise ValueError("Either provider or source_name must be provided.")
        if not self.source_name:
            if self.provider and self.dataset:
                self.source_name = f"{self.provider} - {self.dataset}"
            else:
                self.source_name = self.provider or self.dataset
        if not self.provider:
            self.provider = self.source_name
        if not self.dataset:
            self.dataset = self.source_name


class SourceResponse(SourceContract):
    """API response for a single source, including computed freshness."""

    provider: str = Field(..., min_length=2, max_length=120)
    dataset: str = Field(..., min_length=2, max_length=120)
    freshness: FreshnessStatus
    last_fetched_at: AwareDatetime | None = None
    created_at: AwareDatetime


class SourceListResponse(BaseModel):
    """Paginated list of sources."""

    total: int
    items: list[SourceResponse]


def compute_freshness(
    update_frequency_minutes: int,
    last_fetched_at: datetime | None,
    *,
    now: datetime | None = None,
) -> FreshnessStatus:
    """Determine freshness status from update cadence and last fetch time.

    A source is FRESH if data was fetched within 1.5× its declared cadence,
    STALE if beyond that window, and UNKNOWN if never fetched.
    """
    if last_fetched_at is None:
        return FreshnessStatus.UNKNOWN
    reference = now or datetime.now(UTC)
    if last_fetched_at.tzinfo is None:
        last_fetched_at = last_fetched_at.replace(tzinfo=UTC)
    elapsed_minutes = (reference - last_fetched_at).total_seconds() / 60.0
    threshold = update_frequency_minutes * 1.5
    if elapsed_minutes <= threshold:
        return FreshnessStatus.FRESH
    return FreshnessStatus.STALE
