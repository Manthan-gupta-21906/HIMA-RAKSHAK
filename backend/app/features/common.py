"""Shared temporal cutoff, freshness, and aggregation helpers for feature pipelines."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from app.features.metadata import FeatureDefinition, FeatureValue
from app.schemas.common import FreshnessStatus, ensure_timezone_aware
from app.schemas.observation import ObservationContract, ObservationMetric
from app.schemas.source import compute_freshness

DEFAULT_CADENCE_MINUTES = 60


def filter_observations_in_window(
    observations: Sequence[ObservationContract],
    location_id: str,
    cutoff_at: datetime,
    *,
    metric: ObservationMetric | None = None,
    window_hours: int | None = None,
    end_offset_hours: int = 0,
) -> list[ObservationContract]:
    """Filter observations to a location and strict prediction-time window.

    No observation with ``observed_at > cutoff_at`` is ever returned.
    """
    ensure_timezone_aware(cutoff_at)
    window_end = cutoff_at - timedelta(hours=end_offset_hours)
    window_start = (
        cutoff_at - timedelta(hours=window_hours) if window_hours is not None else None
    )

    matched: list[ObservationContract] = []
    for obs in observations:
        if obs.location_id != location_id:
            continue
        if metric is not None and obs.metric != metric:
            continue
        if obs.observed_at > cutoff_at or obs.observed_at > window_end:
            continue
        if window_start is not None and obs.observed_at < window_start:
            continue
        matched.append(obs)

    matched.sort(key=lambda o: o.observed_at)
    return matched


def compute_window_freshness(
    observations: Sequence[ObservationContract],
    cutoff_at: datetime,
    source_cadences: dict[str, int] | None = None,
) -> FreshnessStatus:
    """Compute freshness at cutoff from the most recent observation."""
    if not observations:
        return FreshnessStatus.UNKNOWN
    latest = max(observations, key=lambda o: o.observed_at)
    cadence = (source_cadences or {}).get(latest.source_id, DEFAULT_CADENCE_MINUTES)
    return compute_freshness(cadence, latest.observed_at, now=cutoff_at)


def aggregate_overall_freshness(features: Sequence[FeatureValue]) -> FreshnessStatus:
    """Summarize freshness across all dynamic features in a vector."""
    statuses = {f.freshness for f in features if f.window_hours is not None}
    if not statuses or statuses == {FreshnessStatus.UNKNOWN}:
        return FreshnessStatus.UNKNOWN
    if FreshnessStatus.STALE in statuses:
        return FreshnessStatus.STALE
    if FreshnessStatus.FRESH in statuses:
        return FreshnessStatus.FRESH
    return FreshnessStatus.UNKNOWN


def build_feature_value(
    spec: FeatureDefinition,
    value: float | None,
    observations: Sequence[ObservationContract],
    cutoff_at: datetime,
    source_cadences: dict[str, int] | None = None,
) -> FeatureValue:
    """Construct a FeatureValue with provenance and freshness metadata."""
    source_ids = sorted({obs.source_id for obs in observations})
    freshness = (
        compute_window_freshness(observations, cutoff_at, source_cadences)
        if spec.window_hours is not None
        else (FreshnessStatus.FRESH if value is not None else FreshnessStatus.UNKNOWN)
    )
    return FeatureValue(
        name=spec.name,
        value=round(value, 4) if value is not None else None,
        unit=spec.unit,
        window_hours=spec.window_hours,
        is_missing=value is None,
        source_ids=source_ids,
        freshness=freshness,
    )


def compute_rate_of_change(observations: Sequence[ObservationContract]) -> float | None:
    """Compute linear rate of change (units/hour) between earliest and latest obs."""
    if len(observations) < 2:
        return None
    ordered = sorted(observations, key=lambda o: o.observed_at)
    elapsed_hours = (ordered[-1].observed_at - ordered[0].observed_at).total_seconds() / 3600.0
    if elapsed_hours <= 0:
        return None
    return (ordered[-1].value - ordered[0].value) / elapsed_hours
