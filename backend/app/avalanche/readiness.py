"""Avalanche readiness evaluation rules and evidence gating."""

from datetime import UTC, datetime

from app.avalanche.requirements import (
    DEFAULT_AVALANCHE_REQUIREMENTS,
    REASON_MISSING_EVENT_LABELS,
    REASON_MISSING_METEOROLOGY,
    REASON_MISSING_SNOWPACK,
    REASON_MISSING_TERRAIN,
    REASON_STALE_METEOROLOGY,
    REASON_STALE_SNOWPACK,
    REASON_TERRAIN_ONLY,
    AvalancheRequirements,
)
from app.avalanche.status import AvalancheOperationalStatus, AvalancheReadinessAssessment
from app.features.avalanche import AvalancheFeatureVector
from app.schemas.common import FreshnessStatus


def evaluate_avalanche_readiness(
    features: AvalancheFeatureVector,
    historical_event_labels_count: int = 0,
    historical_non_event_labels_count: int = 0,
    requirements: AvalancheRequirements = DEFAULT_AVALANCHE_REQUIREMENTS,
    evaluation_time: datetime | None = None,
) -> AvalancheReadinessAssessment:
    """Evaluate avalanche feature vector against strict evidentiary readiness rules.

    Rules:
    1. Missing or stale snowpack strictly blocks 'supported' status.
    2. Terrain-only inputs (missing snowpack and weather) strictly degrade to 'unsupported'.
    3. Missing or insufficient event labels prevent supervised validation claims.
    4. If snowpack is present and fresh, but verified event labels are missing, status is
       'indicative_screening' (advisory screening only, never claimed as validated forecast).
    """
    eval_time = evaluation_time or datetime.now(UTC)
    reasons: list[str] = []
    missing_reqs: list[str] = []
    limitations: list[str] = []

    # Check snowpack presence and freshness
    snow_missing = features.snow_depth_cm.is_missing and features.new_snow_24h_cm.is_missing
    snow_stale = (
        features.snow_depth_cm.freshness == FreshnessStatus.STALE
        or features.new_snow_24h_cm.freshness == FreshnessStatus.STALE
    )

    # Check terrain presence
    terrain_missing = (
        features.slope_deg.is_missing
        or features.aspect_deg.is_missing
        or features.elevation_m.is_missing
    )

    # Check weather presence and freshness
    met_missing = features.temp_mean_24h_c.is_missing or features.wind_loading_kmh.is_missing
    met_stale = (
        features.temp_mean_24h_c.freshness == FreshnessStatus.STALE
        or features.wind_loading_kmh.freshness == FreshnessStatus.STALE
    )

    # Rule 2: Terrain-only inputs
    is_terrain_only = (not terrain_missing) and snow_missing and met_missing
    if is_terrain_only:
        reasons.append(REASON_TERRAIN_ONLY)
        missing_reqs.extend(["snowpack_telemetry", "meteorological_telemetry"])
        limitations.append("Static slope susceptibility cannot forecast active avalanche hazard.")

    # Rule 1: Snowpack checks
    if snow_missing and not is_terrain_only:
        reasons.append(REASON_MISSING_SNOWPACK)
        missing_reqs.append("snowpack_telemetry")
    elif snow_stale:
        reasons.append(REASON_STALE_SNOWPACK)
        missing_reqs.append("fresh_snowpack_telemetry")

    if terrain_missing and not is_terrain_only:
        reasons.append(REASON_MISSING_TERRAIN)
        missing_reqs.append("terrain_coverage")

    if met_missing and not is_terrain_only:
        reasons.append(REASON_MISSING_METEOROLOGY)
        missing_reqs.append("meteorological_telemetry")
    elif met_stale:
        reasons.append(REASON_STALE_METEOROLOGY)
        missing_reqs.append("fresh_meteorological_telemetry")

    # Rule 3: Event label sufficiency check
    has_sufficient_labels = (
        historical_event_labels_count >= requirements.min_historical_event_labels
        and historical_non_event_labels_count >= requirements.min_historical_non_event_labels
    )
    if not has_sufficient_labels:
        reasons.append(REASON_MISSING_EVENT_LABELS)
        missing_reqs.append("verified_historical_event_labels")
        limitations.append(
            "Lack of certified historical avalanche occurrence records prevents statistical "
            "model calibration or validation claims."
        )

    # Determine status
    if is_terrain_only or (snow_missing and met_missing):
        status = AvalancheOperationalStatus.UNSUPPORTED
        is_validated = False
    elif snow_stale or snow_missing or met_stale or terrain_missing:
        # Severe data deficit or staleness
        status = AvalancheOperationalStatus.UNSUPPORTED
        is_validated = False
    elif not has_sufficient_labels:
        # Data is fresh and complete, but without ground-truth labels we only allow screening
        status = AvalancheOperationalStatus.INDICATIVE_SCREENING
        is_validated = False
        limitations.append("Indicative screening only; not a validated avalanche safety forecast.")
    else:
        # All conditions met: fresh snowpack, meteorology, terrain, and verified event labels
        status = AvalancheOperationalStatus.SUPPORTED
        is_validated = True

    return AvalancheReadinessAssessment(
        location_id=features.location_id,
        evaluated_at=eval_time,
        status=status,
        is_validated_forecast_allowed=is_validated,
        reasons=reasons,
        missing_requirements=missing_reqs,
        limitations=limitations,
    )
