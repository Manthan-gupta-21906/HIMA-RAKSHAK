"""Deterministic J&K pilot location fixtures labelled as demo data."""

from app.models.location import LocationRecord
from app.repositories.location_repository import LocationRepository

PILOT_LOCATIONS: list[LocationRecord] = [
    LocationRecord(
        location_id="JK-SGR-01",
        name="Srinagar — Jhelum Floodplain",
        admin_unit="Srinagar District, J&K",
        latitude=34.0837,
        longitude=74.7973,
        geometry_geojson={"type": "Point", "coordinates": [74.7973, 34.0837]},
        supported_hazards=["flood"],
        coverage_status="supported",
        coverage_note="Demo fixture: rainfall and Jhelum gauge baseline available.",
    ),
    LocationRecord(
        location_id="JK-GUL-01",
        name="Gulmarg — Affarwat Ridge",
        admin_unit="Baramulla District, J&K",
        latitude=34.0484,
        longitude=74.3805,
        geometry_geojson={"type": "Point", "coordinates": [74.3805, 34.0484]},
        supported_hazards=["avalanche"],
        coverage_status="partial",
        coverage_note="Indicative terrain + weather screening; snowpack labels sparse.",
    ),
    LocationRecord(
        location_id="JK-BAN-01",
        name="Banihal — NH-44 Corridor",
        admin_unit="Ramban District, J&K",
        latitude=33.4375,
        longitude=75.1947,
        geometry_geojson={"type": "Point", "coordinates": [75.1947, 33.4375]},
        supported_hazards=["flood", "avalanche"],
        coverage_status="partial",
        coverage_note="Dual-hazard corridor; road exposure tracked with cached telemetry.",
    ),
    LocationRecord(
        location_id="JK-DRS-01",
        name="Drass — Zojila High Pass",
        admin_unit="Kargil / Ganderbal Border Sector",
        latitude=34.4275,
        longitude=75.7525,
        geometry_geojson={"type": "Point", "coordinates": [75.7525, 34.4275]},
        supported_hazards=[],
        coverage_status="unsupported",
        coverage_note="Unsupported: insufficient local sensor and snowpack coverage.",
    ),
]


def seed_locations(repo: LocationRepository) -> int:
    """Idempotently load deterministic pilot locations into the repository.

    Returns the number of newly inserted records.
    """
    inserted = 0
    for loc in PILOT_LOCATIONS:
        if repo.get_by_id(loc.location_id) is None:
            repo.upsert(loc)
            inserted += 1
    return inserted
