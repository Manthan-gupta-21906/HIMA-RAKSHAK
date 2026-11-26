"""Tests for Priority 2 operational completeness features."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models.location import LocationModel
from app.models.source import SourceModel
from app.repositories.alert_repository import AlertRepository
from app.repositories.gis_layer_repository import GisLayerRepository
from app.repositories.location_repository import SqlAlchemyLocationRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_repository import RiskAssessmentRepository
from app.repositories.source_repository import SourceRepository
from app.risk.priority import calculate_priority_assessment
from app.schemas.alert import DeliveryChannel, DeliveryStatus
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.ingestion import IngestionRunStatus
from app.schemas.risk import RiskAssessmentContract
from app.services.alert_delivery import AlertDeliveryDispatcher
from app.services.alert_service import AlertService
from app.services.exposure_service import SpatialExposureService
from app.services.ingestion_scheduler import IngestionScheduler
from app.services.risk_service import RiskService


def test_persisted_historical_replay_reconstruction(db_session):
    """Verify RiskService.get_replay_events reconstructs frames from persisted assessments."""
    loc = LocationModel(
        location_id="JK-SGR-01",
        name="Srinagar",
        admin_unit="Srinagar, J&K",
        latitude=34.0837,
        longitude=74.7973,
        supported_hazards=["flood"],
        coverage_status="supported",
        coverage_note="Pilot hub",
        is_demo_fixture=False,
        provenance="test",
    )
    db_session.add(loc)
    db_session.commit()

    risk_repo = RiskAssessmentRepository(db_session)
    t0 = datetime(2026, 11, 20, 6, 0, tzinfo=UTC)
    prov = ProvenanceMeta(
        source_id="src-cwc-01",
        source_name="CWC Telemetry",
        licence="GODL",
        is_demo_fixture=False,
        ingested_at=t0,
    )
    risk_repo.save_many(
        [
            RiskAssessmentContract(
                risk_id="r-1",
                location_id="JK-SGR-01",
                hazard_type=HazardType.FLOOD,
                risk_class=RiskClass.LOW,
                score=0.25,
                confidence=0.8,
                lead_time_hours=6,
                freshness=FreshnessStatus.FRESH,
                prediction_status=PredictionStatus.READY,
                assessed_at=t0,
                provenance=prov,
            ),
            RiskAssessmentContract(
                risk_id="r-2",
                location_id="JK-SGR-01",
                hazard_type=HazardType.FLOOD,
                risk_class=RiskClass.HIGH,
                score=0.82,
                confidence=0.9,
                lead_time_hours=6,
                freshness=FreshnessStatus.FRESH,
                prediction_status=PredictionStatus.READY,
                assessed_at=t0 + timedelta(hours=12),
                provenance=prov,
            ),
        ]
    )
    db_session.commit()

    service = RiskService(
        risk_repo=risk_repo,
        observation_repo=ObservationRepository(db_session),
        location_repo=SqlAlchemyLocationRepository(db_session),
        source_repo=SourceRepository(db_session),
    )
    events = service.get_replay_events(location_id="JK-SGR-01")
    assert len(events) == 1
    assert events[0].location_id == "JK-SGR-01"
    assert len(events[0].frames) == 2
    assert events[0].frames[0].alert_tier == "Watch"
    assert events[0].frames[1].alert_tier == "High Risk"
    assert events[0].frames[1].phase_label.startswith("T+12h")


def test_managed_gis_layer_replaces_hardcoded_exposure_fixture(db_session):
    """Verify SpatialExposureService loads managed GIS layers from the DB repository."""
    layer_repo = GisLayerRepository(db_session)
    layer_repo.upsert_layer(
        layer_id="managed-sgr-assets",
        name="Managed Srinagar Assets",
        layer_category="exposure",
        description="Official SDMA GIS layer",
        provenance="sdma_gis_2026",
        is_demo_fixture=False,
        source_crs_epsg=4326,
        feature_count=1,
        geojson={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [74.7973, 34.0837]},
                    "properties": {
                        "asset_id": "managed-set-1",
                        "asset_type": "settlement",
                        "name": "Managed Srinagar Ward",
                        "count": 2,
                        "count_type": "verified",
                        "population_affected": 12000,
                        "is_critical": False,
                        "hazards": ["flood"],
                    },
                }
            ],
        },
    )

    loc_repo = SqlAlchemyLocationRepository(db_session)
    loc = loc_repo.get_by_id("JK-SGR-01")
    if loc is None:
        db_session.add(
            LocationModel(
                location_id="JK-SGR-01",
                name="Srinagar",
                admin_unit="Srinagar, J&K",
                latitude=34.0837,
                longitude=74.7973,
                supported_hazards=["flood"],
                coverage_status="supported",
                coverage_note="Pilot hub",
                is_demo_fixture=False,
                provenance="test",
            )
        )
        db_session.commit()
        loc = loc_repo.get_by_id("JK-SGR-01")

    assert loc is not None
    exposure_svc = SpatialExposureService(layer_repo=layer_repo)
    profile = exposure_svc.calculate_exposure(loc)
    assert profile.population_exposed == 12000
    assert profile.settlements_count == 2
    assert profile.assets[0].metadata["layer_id"] == "managed-sgr-assets"


def test_alert_delivery_and_status_tracking(db_session):
    """Verify alert generation dispatches delivery and tracks response codes and retries."""
    db_session.add(
        LocationModel(
            location_id="JK-SGR-01",
            name="Srinagar",
            admin_unit="Srinagar, J&K",
            latitude=34.0837,
            longitude=74.7973,
            supported_hazards=["flood"],
            coverage_status="supported",
            coverage_note="Pilot hub",
            is_demo_fixture=False,
            provenance="test",
        )
    )
    db_session.commit()

    calls: list[str] = []

    def fake_http_post(url: str, _payload: dict, _timeout: float) -> int:
        calls.append(url)
        return 202

    dispatcher = AlertDeliveryDispatcher(http_sender=fake_http_post)
    service = AlertService(AlertRepository(db_session), dispatcher=dispatcher)

    now = datetime.now(UTC)
    assessment = RiskAssessmentContract(
        risk_id="risk-deliv-1",
        location_id="JK-SGR-01",
        hazard_type=HazardType.FLOOD,
        risk_class=RiskClass.HIGH,
        score=0.85,
        confidence=0.9,
        lead_time_hours=6,
        freshness=FreshnessStatus.FRESH,
        prediction_status=PredictionStatus.READY,
        assessed_at=now,
        provenance=ProvenanceMeta(
            source_id="src-cwc-01",
            source_name="CWC",
            licence="GODL",
            is_demo_fixture=False,
            ingested_at=now,
        ),
    )
    exposure = SpatialExposureService().calculate_exposure(
        SqlAlchemyLocationRepository(db_session).get_by_id("JK-SGR-01"),  # type: ignore[arg-type]
        assessment,
    )
    priority = calculate_priority_assessment(assessment, exposure)
    alert = service.generate_for_assessment(assessment, priority)
    assert alert is not None
    assert alert.delivery_status == DeliveryStatus.SENT
    assert len(alert.deliveries) == 1

    retried = service.deliver_alert(
        alert.alert_id,
        channels=[DeliveryChannel.WEBHOOK],
        webhook_url="https://hooks.example.test/alerts",
    )
    assert retried.delivery_status == DeliveryStatus.SENT
    assert calls == ["https://hooks.example.test/alerts"]
    assert retried.deliveries[0].response_code == 202


def test_scheduled_ingestion_retries_and_monitoring(db_session, tmp_path: Path):
    """Verify IngestionScheduler retries transient failures and reports monitoring summary."""
    db_session.add(
        LocationModel(
            location_id="JK-SGR-01",
            name="Srinagar",
            admin_unit="Srinagar, J&K",
            latitude=34.0837,
            longitude=74.7973,
            supported_hazards=["flood"],
            coverage_status="supported",
            coverage_note="Pilot hub",
            is_demo_fixture=False,
            provenance="test",
        )
    )
    db_session.add(
        SourceModel(
            source_id="src-cwc-01",
            source_name="CWC Telemetry",
            provider="CWC",
            dataset="river_levels",
            source_type="hydrology",
            access_mode="sample",
            licence="GODL",
            reference_url="",
            update_frequency_minutes=15,
            trust_classification="authoritative",
            is_authoritative=True,
            is_demo_fixture=True,
            last_fetched_at=None,
        )
    )
    db_session.commit()

    csv_file = tmp_path / "obs.csv"
    csv_file.write_text(
        "location_id,observed_at,metric,value,unit\n"
        "JK-SGR-01,2026-11-26T10:00:00+00:00,river_level,4.2,m\n",
        encoding="utf-8",
    )

    attempts = {"count": 0}

    def flaky_fetcher(_source: SourceModel) -> Path:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("Transient network timeout")
        return csv_file

    scheduler = IngestionScheduler(sleep_fn=lambda _s: None)
    runs = scheduler.run_due_sources(db_session, fetcher=flaky_fetcher)
    assert len(runs) == 1
    assert runs[0].status == IngestionRunStatus.SUCCESS
    assert runs[0].attempts == 2
    assert runs[0].records_ingested == 1

    health = scheduler.get_monitoring_summary(db_session)
    assert health.total_sources == 1
    assert health.fresh_sources == 1
    assert health.recent_success_runs == 1
    assert TestClient(app) is not None
