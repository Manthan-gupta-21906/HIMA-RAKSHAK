"""Unit and integration tests for RiskService multi-hazard assessment execution."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy.orm import Session

from alembic import command
from app.db.session import create_db_engine, get_session_factory
from app.features.metadata import TerrainContext
from app.flood.model import FloodBaselineClassifier
from app.models.location import LocationModel
from app.models.observation import ObservationModel
from app.models.source import SourceModel
from app.repositories.location_repository import SqlAlchemyLocationRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.repositories.source_repository import SourceRepository
from app.schemas.common import HazardType, PredictionStatus, RiskClass
from app.schemas.observation import ObservationMetric
from app.schemas.source import AccessMode, SourceType, TrustClassification
from app.services.location_service import LocationNotFoundError
from app.services.risk_service import RiskService

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _setup_service(
    tmp_path: Path,
    flood_model: FloodBaselineClassifier | None = None,
) -> tuple[RiskService, Session]:
    db_url = f"sqlite:///{tmp_path / 'risk_service.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    engine = create_db_engine(db_url)
    session_factory = get_session_factory(engine)
    session = session_factory()

    session.add(
        LocationModel(
            location_id="JK-SGR-01",
            name="Srinagar — Dal Lake Basin",
            admin_unit="Srinagar District, J&K",
            latitude=34.0837,
            longitude=74.7973,
            geom={"type": "Point", "coordinates": [74.7973, 34.0837]},
            supported_hazards=["flood", "avalanche"],
            coverage_status="supported",
            coverage_note="Pilot zone",
            is_demo_fixture=True,
            provenance="demo_fixture:test",
        )
    )
    session.add(
        SourceModel(
            source_id="src-cwc-01",
            source_name="Central Water Commission",
            provider="CWC",
            dataset="telemetry",
            source_type=SourceType.HYDROLOGY.value,
            trust_classification=TrustClassification.AUTHORITATIVE.value,
            access_mode=AccessMode.LIVE.value,
            update_frequency_minutes=60,
            licence="GODL",
            is_authoritative=True,
            is_demo_fixture=True,
        )
    )
    session.add(
        SourceModel(
            source_id="src-dgre-01",
            source_name="DGRE Snow Telemetry",
            provider="DGRE",
            dataset="snowpack",
            source_type=SourceType.SNOW.value,
            trust_classification=TrustClassification.AUTHORITATIVE.value,
            access_mode=AccessMode.LIVE.value,
            update_frequency_minutes=60,
            licence="GODL",
            is_authoritative=True,
            is_demo_fixture=True,
        )
    )
    session.commit()

    service = RiskService(
        risk_repo=RiskAssessmentRepository(session),
        observation_repo=ObservationRepository(session),
        location_repo=SqlAlchemyLocationRepository(session),
        source_repo=SourceRepository(session),
        flood_model=flood_model,
    )
    return service, session


def _fitted_flood_model() -> FloodBaselineClassifier:
    """Controlled fitted flood model fixture for deterministic testing."""
    model = FloodBaselineClassifier(epochs=20, version="test-flood-v1")
    model.fit(
        [
            [0.0, 5.0, 10.0, 1.0, 0.0, 0.5],
            [40.0, 120.0, 150.0, 5.5, 0.4, 1.5],
        ],
        [0, 1],
        feature_names=[
            "rain_1h_mm",
            "rain_24h_mm",
            "antecedent_rain_72h_mm",
            "river_level_m",
            "river_level_rate_m_per_h",
            "drainage_density",
        ],
    )
    return model


def _seed_observations(session: Session, cutoff: datetime) -> None:
    obs = [
        ObservationModel(
            observation_id="obs-rain-1",
            location_id="JK-SGR-01",
            source_id="src-cwc-01",
            observed_at=cutoff - timedelta(minutes=20),
            metric=ObservationMetric.RAIN_MM.value,
            value=35.0,
            unit="mm",
            idempotency_key="k-rain-1",
            is_demo_fixture=True,
            ingested_at=cutoff,
        ),
        ObservationModel(
            observation_id="obs-river-1",
            location_id="JK-SGR-01",
            source_id="src-cwc-01",
            observed_at=cutoff - timedelta(minutes=15),
            metric=ObservationMetric.RIVER_LEVEL_M.value,
            value=5.2,
            unit="m",
            idempotency_key="k-river-1",
            is_demo_fixture=True,
            ingested_at=cutoff,
        ),
        ObservationModel(
            observation_id="obs-snow-1",
            location_id="JK-SGR-01",
            source_id="src-dgre-01",
            observed_at=cutoff - timedelta(minutes=30),
            metric=ObservationMetric.SNOW_DEPTH_CM.value,
            value=60.0,
            unit="cm",
            idempotency_key="k-snow-1",
            is_demo_fixture=True,
            ingested_at=cutoff,
        ),
        ObservationModel(
            observation_id="obs-snow-2",
            location_id="JK-SGR-01",
            source_id="src-dgre-01",
            observed_at=cutoff - timedelta(minutes=10),
            metric=ObservationMetric.SNOW_DEPTH_CM.value,
            value=72.0,
            unit="cm",
            idempotency_key="k-snow-2",
            is_demo_fixture=True,
            ingested_at=cutoff,
        ),
        ObservationModel(
            observation_id="obs-temp-1",
            location_id="JK-SGR-01",
            source_id="src-dgre-01",
            observed_at=cutoff - timedelta(minutes=10),
            metric=ObservationMetric.TEMP_C.value,
            value=-4.0,
            unit="C",
            idempotency_key="k-temp-1",
            is_demo_fixture=True,
            ingested_at=cutoff,
        ),
        ObservationModel(
            observation_id="obs-wind-1",
            location_id="JK-SGR-01",
            source_id="src-dgre-01",
            observed_at=cutoff - timedelta(minutes=10),
            metric=ObservationMetric.WIND_KMH.value,
            value=32.0,
            unit="km/h",
            idempotency_key="k-wind-1",
            is_demo_fixture=True,
            ingested_at=cutoff,
        ),
    ]
    session.add_all(obs)
    session.commit()


def test_assess_flood_without_model_is_unsupported(tmp_path: Path) -> None:
    service, session = _setup_service(tmp_path, flood_model=None)
    cutoff = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    _seed_observations(session, cutoff)

    state = service.assess_location_risk("JK-SGR-01", cutoff_at=cutoff)

    assert state.flood is not None
    assert state.flood.prediction_status == PredictionStatus.UNSUPPORTED
    assert state.flood.risk_class == RiskClass.UNSUPPORTED
    assert state.flood.score is None
    assert state.flood.provenance.source_id == "src-cwc-01"


def test_assess_flood_with_unfitted_model_is_unsupported(tmp_path: Path) -> None:
    unfitted = FloodBaselineClassifier()
    service, session = _setup_service(tmp_path, flood_model=unfitted)
    cutoff = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    _seed_observations(session, cutoff)

    state = service.assess_location_risk("JK-SGR-01", cutoff_at=cutoff)

    assert state.flood is not None
    assert state.flood.prediction_status == PredictionStatus.UNSUPPORTED
    assert state.flood.score is None


def test_assess_flood_with_fitted_model_fixture_produces_ready_prediction(
    tmp_path: Path,
) -> None:
    model = _fitted_flood_model()
    service, session = _setup_service(tmp_path, flood_model=model)
    cutoff = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    _seed_observations(session, cutoff)

    state = service.assess_location_risk("JK-SGR-01", cutoff_at=cutoff)

    assert state.flood is not None
    assert state.flood.hazard_type == HazardType.FLOOD
    assert state.flood.prediction_status == PredictionStatus.READY
    assert state.flood.score is not None
    assert 0.0 <= state.flood.score <= 1.0
    assert state.flood.model_version == "test-flood-v1"
    assert state.flood.provenance.source_id == "src-cwc-01"


def test_assess_avalanche_insufficient_readiness_states(tmp_path: Path) -> None:
    service, session = _setup_service(tmp_path)
    cutoff = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)

    # 1. No observations and no terrain -> UNSUPPORTED
    state_empty = service.assess_location_risk("JK-SGR-01", cutoff_at=cutoff)
    assert state_empty.avalanche is not None
    assert state_empty.avalanche.prediction_status == PredictionStatus.UNSUPPORTED
    assert state_empty.avalanche.risk_class == RiskClass.UNSUPPORTED
    assert state_empty.avalanche.score is None
    assert state_empty.avalanche.provenance.source_id == "internal-pipeline"

    # 2. Fresh snowpack + weather + terrain, but 0 historical event labels -> INDICATIVE
    _seed_observations(session, cutoff)
    terrain = TerrainContext(elevation_m=3200.0, slope_deg=35.0, aspect_deg=120.0)
    state_indicative = service.assess_location_risk(
        "JK-SGR-01",
        cutoff_at=cutoff + timedelta(minutes=1),
        terrain=terrain,
        historical_event_labels_count=0,
    )
    assert state_indicative.avalanche is not None
    assert state_indicative.avalanche.prediction_status == PredictionStatus.INDICATIVE
    assert state_indicative.avalanche.provenance.source_id == "src-dgre-01"
    assert "historical" in (state_indicative.avalanche.readiness_reason or "").lower()


def test_assess_location_risk_persists_and_is_retrievable(tmp_path: Path) -> None:
    model = _fitted_flood_model()
    service, session = _setup_service(tmp_path, flood_model=model)
    cutoff = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    _seed_observations(session, cutoff)

    state = service.assess_location_risk("JK-SGR-01", cutoff_at=cutoff)
    session.commit()

    current = service.get_current_risk("JK-SGR-01")
    assert current["flood"] is not None
    assert current["flood"].risk_id == state.flood.risk_id  # type: ignore[union-attr]
    assert current["avalanche"] is not None
    assert current["avalanche"].risk_id == state.avalanche.risk_id  # type: ignore[union-attr]

    history, total, _ = service.get_risk_history("JK-SGR-01")
    assert total == 2
    assert {item.hazard_type for item in history} == {
        HazardType.FLOOD,
        HazardType.AVALANCHE,
    }


def test_assess_missing_location_raises_not_found(tmp_path: Path) -> None:
    service, _ = _setup_service(tmp_path)
    with pytest.raises(LocationNotFoundError):
        service.assess_location_risk("JK-DOES-NOT-EXIST")
