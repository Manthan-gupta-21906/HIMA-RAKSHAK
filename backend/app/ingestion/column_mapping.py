"""Configurable CSV column mapping, normalization, and idempotency keys."""

import hashlib
from datetime import UTC, datetime

from pydantic import BaseModel

from app.schemas.observation import ALLOWED_UNITS, ObservationMetric


class ColumnMapping(BaseModel):
    """Maps CSV header names to canonical ObservationContract fields."""

    location_id: str = "location_id"
    observed_at: str = "observed_at"
    metric: str = "metric"
    value: str = "value"
    unit: str = "unit"
    observation_id: str | None = "observation_id"


def parse_aware_timestamp(raw: str) -> datetime:
    """Parse an ISO-8601 timestamp string, requiring timezone info."""
    cleaned = raw.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"Timestamp '{raw}' must include timezone offset.")
    return dt.astimezone(UTC)


def normalize_unit_and_value(
    metric: ObservationMetric, raw_value: float, raw_unit: str
) -> tuple[float, str]:
    """Normalize common unit variants to canonical metric units."""
    unit = raw_unit.strip()
    expected = ALLOWED_UNITS[metric]
    if unit == expected:
        return raw_value, expected

    if metric == ObservationMetric.TEMP_C and unit.lower() in {"degc", "°c", "c"}:
        return raw_value, "C"
    if metric == ObservationMetric.WIND_KMH and unit.lower() in {"m/s", "mps"}:
        return round(raw_value * 3.6, 4), "km/h"
    if metric == ObservationMetric.RAIN_MM and unit.lower() == "cm":
        return round(raw_value * 10.0, 4), "mm"
    if metric == ObservationMetric.SNOW_DEPTH_CM and unit.lower() == "mm":
        return round(raw_value / 10.0, 4), "cm"
    return raw_value, unit


def compute_idempotency_key(
    location_id: str,
    source_id: str,
    observed_at: datetime,
    metric: str,
) -> str:
    """Compute a deterministic SHA-256 key for an observation."""
    utc_ts = observed_at.astimezone(UTC).isoformat()
    payload = f"{location_id}|{source_id}|{utc_ts}|{metric}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
