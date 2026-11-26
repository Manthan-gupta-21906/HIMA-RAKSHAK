"""Tests for RiskOrchestrator multi-hazard coordination without blending hazard pipelines."""

from datetime import UTC, datetime
from pathlib import Path

from alembic.config import Config
from sqlalchemy.orm import Session

from alembic import command
from app.db.session import create_db_engine, get_session_factory
from app.features.avalanche import AvalancheFeatureVector
from app.features.flood import FloodFeatureVector
from app.features.metadata import FeatureValue
from app.flood.model import FloodBaselineClassifier
from app.models.location import LocationModel
from app.repositories.risk_repository import RiskAssessmentRepository
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    RiskClass,
)
from app.services.risk_orchestrator import RiskOrchestrator

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _setup_orchestrator(tmp_path: Path) -> tuple[RiskOrchestrator, Session]:
    db_url = f"sqlite:///{tmp_path / 'orch.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    loc = LocationModel(
        location_id="loc-kullu-01",
        name="Kullu Pilot Zone",
        admin_unit="Kullu, HP",
        latitude=31.95,
        longitude=77.10,
        geom={"type": "Point", "coordinates": [77.10, 31.95]},
        supported_hazards=["flood", "avalanche"],
        coverage_status="supported",
        coverage_note="Fully covered pilot zone",
        is_demo_fixture=True,
        provenance="demo_fixture:test",
    )
    session.add(loc)
    session.commit()

    repo = RiskAssessmentRepository(session)
    return RiskOrchestrator(repo), session


def _dummy_flood_vector(cutoff_at: datetime) -> FloodFeatureVector:
    return FloodFeatureVector(
        location_id="loc-kullu-01",
        cutoff_at=cutoff_at,
        rain_1h_mm=FeatureValue(name="rain_1h_mm", value=35.0, unit="mm", is_missing=False),
        rain_24h_mm=FeatureValue(name="rain_24h_mm", value=80.0, unit="mm", is_missing=False),
        antecedent_rain_72h_mm=FeatureValue(
            name="antecedent_rain_72h_mm", value=110.0, unit="mm", is_missing=False
        ),
        river_level_m=FeatureValue(name="river_level_m", value=4.8, unit="m", is_missing=False),
        river_level_rate_m_per_h=FeatureValue(
            name="river_level_rate_m_per_h", value=0.3, unit="m/h", is_missing=False
        ),
        drainage_density=FeatureValue(
            name="drainage_density", value=1.5, unit="km/km2", is_missing=False
        ),
        missing_count=0,
        overall_freshness=FreshnessStatus.FRESH,
    )


def _dummy_avalanche_vector(
    cutoff_at: datetime,
    is_terrain_only: bool = False,
    snow_freshness: FreshnessStatus = FreshnessStatus.FRESH,
) -> AvalancheFeatureVector:
    snow_val = None if is_terrain_only else 65.0
    return AvalancheFeatureVector(
        hazard_type=HazardType.AVALANCHE,
        location_id="loc-kullu-01",
        cutoff_at=cutoff_at,
        new_snow_24h_cm=FeatureValue(
            name="new_snow_24h_cm",
            value=None if is_terrain_only else 12.0,
            unit="cm",
            is_missing=is_terrain_only,
            freshness=snow_freshness,
        ),
        snow_depth_cm=FeatureValue(
            name="snow_depth_cm",
            value=snow_val,
            unit="cm",
            is_missing=is_terrain_only,
            freshness=snow_freshness,
        ),
        swe_estimate_mm=FeatureValue(
            name="swe_estimate_mm",
            value=snow_val * 2.5 if snow_val else None,
            unit="mm",
            is_missing=is_terrain_only,
            freshness=snow_freshness,
        ),
        temp_mean_24h_c=FeatureValue(
            name="temp_mean_24h_c",
            value=None if is_terrain_only else -3.0,
            unit="c",
            is_missing=is_terrain_only,
        ),
        wind_loading_kmh=FeatureValue(
            name="wind_loading_kmh",
            value=None if is_terrain_only else 28.0,
            unit="km/h",
            is_missing=is_terrain_only,
        ),
        slope_deg=FeatureValue(name="slope_deg", value=36.0, unit="deg", is_missing=False),
        aspect_deg=FeatureValue(name="aspect_deg", value=90.0, unit="deg", is_missing=False),
        elevation_m=FeatureValue(name="elevation_m", value=3250.0, unit="m", is_missing=False),
        missing_count=5 if is_terrain_only else 0,
        overall_freshness=snow_freshness,
    )


def test_orchestration_flood_and_avalanche_independent_co_located(tmp_path: Path):
    """Verify orchestrator coordinates separate hazard assessments into unified spatial state."""
    orch, session = _setup_orchestrator(tmp_path)
    now = datetime(2026, 11, 26, 14, 0, tzinfo=UTC)

    # 1. Assess flood with fitted baseline model
    model = FloodBaselineClassifier(epochs=10)
    # Train minimally on dummy data
    model.fit(
        [[10.0, 20.0, 30.0, 2.0, 0.1, 1.0], [50.0, 100.0, 150.0, 5.0, 0.5, 1.0]],
        [0, 1],
        feature_names=["r1", "r24", "ant", "riv", "rate", "drain"],
    )
    flood_vec = _dummy_flood_vector(now)
    flood_assessment = orch.assess_flood(flood_vec, model=model)

    assert flood_assessment.hazard_type == HazardType.FLOOD
    assert flood_assessment.prediction_status == PredictionStatus.READY
    assert flood_assessment.score is not None

    # 2. Assess avalanche (fresh telemetry, but unverified event labels -> indicative)
    avalanche_vec = _dummy_avalanche_vector(now)
    avalanche_assessment = orch.assess_avalanche(
        avalanche_vec, historical_event_labels_count=0
    )

    assert avalanche_assessment.hazard_type == HazardType.AVALANCHE
    assert avalanche_assessment.prediction_status == PredictionStatus.INDICATIVE
    assert (
        "verified historical avalanche" in str(avalanche_assessment.readiness_reason).lower()
        or "indicative" in str(avalanche_assessment.readiness_reason).lower()
    )

    # 3. Retrieve co-located spatial state
    state = orch.get_location_risk_state("loc-kullu-01")

    assert state.location_id == "loc-kullu-01"
    assert state.flood is not None
    assert state.avalanche is not None
    # Outputs are distinct, not blended
    assert state.flood.hazard_type == HazardType.FLOOD
    assert state.avalanche.hazard_type == HazardType.AVALANCHE
    assert state.highest_risk_class in [RiskClass.MODERATE, RiskClass.HIGH, RiskClass.SEVERE]


def test_orchestration_unsupported_states_persist_no_fake_scores(tmp_path: Path):
    """Verify terrain-only avalanche and uncalibrated flood yield unsupported with score=None."""
    orch, session = _setup_orchestrator(tmp_path)
    now = datetime(2026, 11, 26, 14, 0, tzinfo=UTC)

    # Uncalibrated flood (model=None)
    flood_assessment = orch.assess_flood(_dummy_flood_vector(now), model=None)
    assert flood_assessment.prediction_status == PredictionStatus.UNSUPPORTED
    assert flood_assessment.risk_class == RiskClass.UNSUPPORTED
    assert flood_assessment.score is None

    # Terrain-only avalanche
    avalanche_vec = _dummy_avalanche_vector(now, is_terrain_only=True)
    avalanche_assessment = orch.assess_avalanche(avalanche_vec)
    assert avalanche_assessment.prediction_status == PredictionStatus.UNSUPPORTED
    assert avalanche_assessment.risk_class == RiskClass.UNSUPPORTED
    assert avalanche_assessment.score is None


def test_orchestration_determinism(tmp_path: Path):
    """Verify orchestrator runs produce deterministic outputs given identical inputs."""
    orch, session = _setup_orchestrator(tmp_path)
    now = datetime(2026, 11, 26, 15, 0, tzinfo=UTC)

    vec1 = _dummy_flood_vector(now)
    vec2 = _dummy_flood_vector(now)

    res1 = orch.assess_flood(vec1, model=None)
    res2 = orch.assess_flood(vec2, model=None)

    assert res1.risk_id == res2.risk_id
    assert res1.risk_class == res2.risk_class
    assert res1.prediction_status == res2.prediction_status
