"""Spatial exposure aggregation and asset intersection logic."""

from datetime import UTC, datetime

from app.schemas.exposure import (
    ExposureAsset,
    ExposureCoverageStatus,
    LocationExposureProfile,
)

REQUIRED_EXPOSURE_LAYERS = ["settlements", "homes", "roads", "critical_facilities"]


def build_exposure_profile(
    location_id: str,
    assets: list[ExposureAsset],
    available_layers: list[str] | None = None,
    evaluated_at: datetime | None = None,
) -> LocationExposureProfile:
    """Aggregate individual intersecting assets into a location exposure profile."""
    eval_time = evaluated_at or datetime.now(UTC)
    avail = set(available_layers or [a.asset_type for a in assets])

    missing = [layer for layer in REQUIRED_EXPOSURE_LAYERS if layer not in avail]

    if not avail:
        coverage = ExposureCoverageStatus.UNKNOWN
    elif missing:
        coverage = ExposureCoverageStatus.PARTIAL
    else:
        coverage = ExposureCoverageStatus.COMPLETE

    pop_total = 0
    settlements = 0
    homes = 0
    roads_km = 0.0
    crit_count = 0

    for a in assets:
        pop_total += a.population_affected
        if a.asset_type == "settlement":
            settlements += a.count
        elif a.asset_type == "home":
            homes += a.count
        elif a.asset_type == "road":
            km = float(a.metadata.get("length_km", a.count))
            roads_km += km
        elif a.asset_type == "critical_facility" or a.is_critical:
            crit_count += a.count

    return LocationExposureProfile(
        location_id=location_id,
        evaluated_at=eval_time,
        coverage_status=coverage,
        population_exposed=pop_total,
        settlements_count=settlements,
        homes_exposed=homes,
        roads_exposed_km=round(roads_km, 2),
        critical_facilities_count=crit_count,
        assets=assets,
        missing_layers=missing,
    )
