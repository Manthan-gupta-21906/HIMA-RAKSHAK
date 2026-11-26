"""Idempotent seed script to initialize demo data in the database.

Seeds:
1. Demo users (admin, operator, viewer)
2. Pilot locations (JK-SGR-01, JK-GUL-01, JK-BAN-01, JK-DRS-01)
3. Essential sources (telemetry, field observations, weather, flood, avalanche)
4. Sample observations from CSV or demo sets
5. Sample official warning fixtures (CWC, DGRE, IMD)
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.api.routes.auth import seed_demo_users
from app.db.session import create_db_engine, get_session_factory
from app.ingestion.warning_import import import_sample_fixtures
from app.models.location import LocationModel
from app.models.observation import ObservationModel
from app.models.source import SourceModel
from app.seed.locations import PILOT_LOCATIONS

logger = logging.getLogger(__name__)


def seed_pilot_locations(db: Session) -> int:
    """Ensure pilot locations are persisted in the database."""
    inserted = 0
    for loc in PILOT_LOCATIONS:
        row = db.get(LocationModel, loc.location_id)
        if row is None:
            geom = loc.geometry_geojson or {
                "type": "Point",
                "coordinates": [loc.longitude, loc.latitude],
            }
            row = LocationModel(
                location_id=loc.location_id,
                name=loc.name,
                admin_unit=loc.admin_unit,
                latitude=loc.latitude,
                longitude=loc.longitude,
                geom=geom,
                supported_hazards=list(loc.supported_hazards),
                coverage_status=loc.coverage_status,
                coverage_note=loc.coverage_note,
                is_demo_fixture=loc.is_demo_fixture,
                provenance=loc.provenance,
            )
            db.add(row)
            inserted += 1
    db.flush()
    return inserted


def seed_sources(db: Session) -> int:
    """Ensure baseline telemetry and agency sources exist."""
    sources_data = [
        {
            "source_id": "src-cwc-01",
            "source_name": "Central Water Commission Telemetry",
            "provider": "Central Water Commission (CWC)",
            "dataset": "river_levels_telemetry",
            "source_type": "hydrology",
            "access_mode": "live",
            "licence": "Government Open Data Licence - India (GODL)",
            "reference_url": "https://cwc.gov.in/",
            "update_frequency_minutes": 15,
            "trust_classification": "authoritative",
            "is_authoritative": True,
            "is_demo_fixture": True,
        },
        {
            "source_id": "src-field-obs",
            "source_name": "Field Observation Network",
            "provider": "HIMA-RAKSHAK Field Observers",
            "dataset": "field_observations",
            "source_type": "field_observation",
            "access_mode": "manual",
            "licence": "Internal System Licence",
            "reference_url": "https://himarakshak.local/",
            "update_frequency_minutes": 60,
            "trust_classification": "field",
            "is_authoritative": False,
            "is_demo_fixture": True,
        },
        {
            "source_id": "src-dgre-01",
            "source_name": "DGRE Snow & Avalanche Telemetry",
            "provider": "Defence Geoinformatics Research Establishment (DGRE)",
            "dataset": "snowpack_and_weather",
            "source_type": "snowpack",
            "access_mode": "live",
            "licence": "Government Open Data Licence - India (GODL)",
            "reference_url": "https://dgre.drdo.gov.in/",
            "update_frequency_minutes": 30,
            "trust_classification": "authoritative",
            "is_authoritative": True,
            "is_demo_fixture": True,
        },
        {
            "source_id": "src-imd-01",
            "source_name": "IMD Automated Weather Station",
            "provider": "India Meteorological Department (IMD)",
            "dataset": "surface_weather_telemetry",
            "source_type": "weather",
            "access_mode": "live",
            "licence": "Government Open Data Licence - India (GODL)",
            "reference_url": "https://mausam.imd.gov.in/",
            "update_frequency_minutes": 60,
            "trust_classification": "authoritative",
            "is_authoritative": True,
            "is_demo_fixture": True,
        },
    ]
    inserted = 0
    now = datetime.now(UTC)
    for s in sources_data:
        row = db.get(SourceModel, s["source_id"])
        if row is None:
            db.add(
                SourceModel(
                    source_id=s["source_id"],
                    source_name=s["source_name"],
                    provider=s["provider"],
                    dataset=s["dataset"],
                    source_type=s["source_type"],
                    access_mode=s["access_mode"],
                    licence=s["licence"],
                    reference_url=s["reference_url"],
                    update_frequency_minutes=s["update_frequency_minutes"],
                    trust_classification=s["trust_classification"],
                    is_authoritative=s["is_authoritative"],
                    is_demo_fixture=s["is_demo_fixture"],
                    last_fetched_at=now,
                    created_at=now,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def seed_demo_observations(db: Session) -> int:
    """Seed baseline observations for pilot locations."""
    now = datetime.now(UTC)
    obs_fixtures = [
        ("obs-sgr-01", "JK-SGR-01", "src-cwc-01", now - timedelta(hours=1), "rain_mm", 45.2, "mm"),
        (
            "obs-sgr-02",
            "JK-SGR-01",
            "src-cwc-01",
            now - timedelta(hours=1),
            "river_level_m",
            4.8,
            "m",
        ),
        (
            "obs-gul-01",
            "JK-GUL-01",
            "src-dgre-01",
            now - timedelta(hours=1),
            "snow_depth_cm",
            110.0,
            "cm",
        ),
        (
            "obs-gul-02",
            "JK-GUL-01",
            "src-dgre-01",
            now - timedelta(hours=1),
            "wind_kmh",
            55.0,
            "km/h",
        ),
        (
            "obs-ban-01",
            "JK-BAN-01",
            "src-imd-01",
            now - timedelta(hours=2),
            "rain_mm",
            32.0,
            "mm",
        ),
        (
            "obs-ban-02",
            "JK-BAN-01",
            "src-dgre-01",
            now - timedelta(hours=2),
            "snow_depth_cm",
            35.0,
            "cm",
        ),
    ]
    inserted = 0
    for obs_id, loc_id, src_id, obs_time, metric, val, unit in obs_fixtures:
        row = db.get(ObservationModel, obs_id)
        if row is None:
            db.add(
                ObservationModel(
                    observation_id=obs_id,
                    location_id=loc_id,
                    source_id=src_id,
                    observed_at=obs_time,
                    metric=metric,
                    value=val,
                    unit=unit,
                    idempotency_key=f"init-{obs_id}",
                    is_demo_fixture=True,
                    ingested_at=now,
                )
            )
            inserted += 1
    db.flush()
    return inserted


def seed_all_demo_data(db: Session) -> dict[str, int]:
    """Execute all seeders in order within a single transaction."""
    users = seed_demo_users(db)
    locations = seed_pilot_locations(db)
    sources = seed_sources(db)
    observations = seed_demo_observations(db)
    warnings = len(import_sample_fixtures(db))
    db.commit()
    return {
        "users": users,
        "locations": locations,
        "sources": sources,
        "observations": observations,
        "warnings": warnings,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing database with demo data...")
    engine = create_db_engine()
    factory = get_session_factory(engine)
    with factory() as db:
        results = seed_all_demo_data(db)
        logger.info("Demo data initialization complete: %s", results)


if __name__ == "__main__":
    main()
