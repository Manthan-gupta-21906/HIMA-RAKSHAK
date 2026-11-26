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
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.ingestion.warning_import import (
    import_warning_record,
    load_sample_warning_fixtures,
)
from app.models.alert import AlertActionModel  # noqa: F401
from app.models.location import LocationModel
from app.models.observation import ObservationModel
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.models.source import SourceModel
from app.models.user import UserModel, UserRole
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.risk import RiskAssessmentContract
from app.seed.locations import PILOT_LOCATIONS

logger = logging.getLogger(__name__)


def seed_demo_users(db: Session) -> int:
    """Ensure standard demo users exist for testing and demo flows."""
    demo_users = [
        ("Admin", "Admin123", "Demo Admin", UserRole.ADMIN),
        ("operator", "operator1234", "Demo Operator", UserRole.DISTRICT_OPERATOR),
        ("viewer", "viewer1234", "Demo Viewer", UserRole.VIEWER),
    ]
    inserted = 0
    legacy_admin = (
        db.query(UserModel)
        .filter(UserModel.username == "admin", UserModel.is_demo_fixture.is_(True))
        .first()
    )
    if legacy_admin is not None:
        existing_upper = db.query(UserModel).filter(UserModel.username == "Admin").first()
        if existing_upper is None:
            legacy_admin.username = "Admin"
            legacy_admin.hashed_password = hash_password("Admin123")
            inserted += 1
        else:
            db.delete(legacy_admin)
        db.flush()

    for username, password, full_name, role in demo_users:
        user = db.query(UserModel).filter(UserModel.username == username).first()
        if user is None:
            db.add(
                UserModel(
                    user_id=str(uuid4()),
                    username=username,
                    hashed_password=hash_password(password),
                    full_name=full_name,
                    role=role,
                    is_demo_fixture=True,
                )
            )
            inserted += 1
    db.flush()
    return inserted


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


def seed_demo_risk_assessments(db: Session) -> int:
    """Seed baseline hazard assessments for pilot locations keeping flood and avalanche distinct."""
    repo = RiskAssessmentRepository(db)
    now = datetime.now(UTC)

    cwc_meta = ProvenanceMeta(
        source_id="src-cwc-01",
        source_name="Central Water Commission Telemetry",
        licence="Government Open Data Licence - India (GODL)",
        is_demo_fixture=True,
        ingested_at=now,
    )
    dgre_meta = ProvenanceMeta(
        source_id="src-dgre-01",
        source_name="DGRE Snow & Avalanche Telemetry",
        licence="Government Open Data Licence - India (GODL)",
        is_demo_fixture=True,
        ingested_at=now,
    )
    imd_meta = ProvenanceMeta(
        source_id="src-imd-01",
        source_name="IMD Automated Weather Station",
        licence="Government Open Data Licence - India (GODL)",
        is_demo_fixture=True,
        ingested_at=now,
    )

    contracts = [
        RiskAssessmentContract(
            risk_id="risk-demo-flood-sgr-01",
            location_id="JK-SGR-01",
            hazard_type=HazardType.FLOOD,
            risk_class=RiskClass.MODERATE,
            score=0.62,
            confidence=0.82,
            lead_time_hours=24,
            freshness=FreshnessStatus.FRESH,
            prediction_status=PredictionStatus.READY,
            readiness_reason=None,
            assessed_at=now - timedelta(minutes=15),
            model_version="flood-baseline-v1",
            provenance=cwc_meta,
        ),
        RiskAssessmentContract(
            risk_id="risk-demo-avalanche-gul-01",
            location_id="JK-GUL-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.MODERATE,
            score=0.50,
            confidence=0.30,
            lead_time_hours=12,
            freshness=FreshnessStatus.FRESH,
            prediction_status=PredictionStatus.INDICATIVE,
            readiness_reason="Indicative terrain + weather screening; snowpack labels sparse.",
            assessed_at=now - timedelta(minutes=20),
            model_version="readiness-gated-v1",
            provenance=dgre_meta,
        ),
        RiskAssessmentContract(
            risk_id="risk-demo-flood-ban-01",
            location_id="JK-BAN-01",
            hazard_type=HazardType.FLOOD,
            risk_class=RiskClass.MODERATE,
            score=0.48,
            confidence=0.65,
            lead_time_hours=24,
            freshness=FreshnessStatus.STALE,
            prediction_status=PredictionStatus.STALE,
            readiness_reason="Cached telemetry; awaiting fresh IMD rainfall feed.",
            assessed_at=now - timedelta(hours=2),
            model_version="flood-baseline-v1",
            provenance=imd_meta,
        ),
        RiskAssessmentContract(
            risk_id="risk-demo-avalanche-ban-01",
            location_id="JK-BAN-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.MODERATE,
            score=0.50,
            confidence=0.30,
            lead_time_hours=12,
            freshness=FreshnessStatus.STALE,
            prediction_status=PredictionStatus.INDICATIVE,
            readiness_reason="Indicative screening only; insufficient historical avalanche labels.",
            assessed_at=now - timedelta(hours=2),
            model_version="readiness-gated-v1",
            provenance=dgre_meta,
        ),
        RiskAssessmentContract(
            risk_id="risk-demo-avalanche-drs-01",
            location_id="JK-DRS-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.UNSUPPORTED,
            score=None,
            confidence=0.0,
            lead_time_hours=12,
            freshness=FreshnessStatus.UNKNOWN,
            prediction_status=PredictionStatus.UNSUPPORTED,
            readiness_reason="Unsupported: insufficient local sensor and snowpack coverage.",
            assessed_at=now - timedelta(hours=1),
            model_version=None,
            provenance=dgre_meta,
        ),
    ]

    inserted = 0
    for contract in contracts:
        existing = repo.get_latest_for_location_and_hazard(
            contract.location_id, contract.hazard_type
        )
        if existing is None:
            repo.save(contract)
            inserted += 1
    db.flush()
    return inserted


def seed_all_demo_data(db: Session) -> dict[str, int]:
    """Execute all seeders in order within a single transaction."""
    users = seed_demo_users(db)
    locations = seed_pilot_locations(db)
    sources = seed_sources(db)
    observations = seed_demo_observations(db)
    warnings = 0
    for fixture in load_sample_warning_fixtures():
        if db.get(LocationModel, fixture.location_id) is None:
            fixture = fixture.model_copy(update={"location_id": "JK-SGR-01"})
        import_warning_record(db, fixture)
        warnings += 1
    risk_assessments = seed_demo_risk_assessments(db)
    db.commit()
    return {
        "users": users,
        "locations": locations,
        "sources": sources,
        "observations": observations,
        "warnings": warnings,
        "risk_assessments": risk_assessments,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Initializing database with demo data...")
    engine = create_db_engine()
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory(engine)
    with factory() as db:
        results = seed_all_demo_data(db)
        logger.info("Demo data initialization complete: %s", results)


if __name__ == "__main__":
    main()
