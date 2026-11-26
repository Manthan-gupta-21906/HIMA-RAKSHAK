"""Impact index computation from exposed population and critical assets."""

from app.schemas.exposure import LocationExposureProfile

# Documented and audited weights for human and infrastructure impact indicators
DEFAULT_IMPACT_WEIGHTS: dict[str, float] = {
    "population": 0.40,
    "critical_facilities": 0.30,
    "homes": 0.15,
    "roads": 0.15,
}

# Normalization caps for regional pilot scale
CAP_POPULATION = 10000.0
CAP_CRITICAL_FACILITIES = 10.0
CAP_HOMES = 2000.0
CAP_ROADS_KM = 50.0


def compute_impact_score(
    profile: LocationExposureProfile,
    weights: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    """Calculate normalized impact score in [0.0, 1.0] and component breakdown.

    Notice that this score strictly reflects exposure / consequence magnitude,
    and does NOT alter or blend the physical hazard score.
    """
    w = weights or DEFAULT_IMPACT_WEIGHTS

    norm_pop = min(1.0, profile.population_exposed / CAP_POPULATION)
    norm_crit = min(1.0, profile.critical_facilities_count / CAP_CRITICAL_FACILITIES)
    norm_homes = min(1.0, profile.homes_exposed / CAP_HOMES)
    norm_roads = min(1.0, profile.roads_exposed_km / CAP_ROADS_KM)

    breakdown = {
        "norm_population": round(norm_pop, 4),
        "norm_critical_facilities": round(norm_crit, 4),
        "norm_homes": round(norm_homes, 4),
        "norm_roads": round(norm_roads, 4),
    }

    score = (
        (w["population"] * norm_pop)
        + (w["critical_facilities"] * norm_crit)
        + (w["homes"] * norm_homes)
        + (w["roads"] * norm_roads)
    )

    return round(min(1.0, max(0.0, score)), 4), breakdown
