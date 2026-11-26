"""End-to-end integration test for the full hazard observation-to-alert workflow.

Flow verified:
1. Submit an observation (POST /observations) -> verify persistence (GET /observations)
2. Execute controlled assessment workflow (POST /risk/evaluate/{location_id})
   -> verify persisted assessment (GET /risk/state/{location_id}, GET /risk/current/{location_id})
3. Verify spatial exposure analysis (GET /risk/exposure/{location_id})
4. Verify explainable risk prioritization (GET /risk/priority/{location_id})
5. Verify persisted alert & action history (/alerts, /acknowledge, /action)
6. Verify authoritative official warnings (GET /warnings) remain distinct and read-only.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.alert import AlertActionModel  # noqa: F401
from app.models.observation import ObservationModel  # noqa: F401
from app.models.official_warning import OfficialWarningModel  # noqa: F401
from app.models.risk_assessment import RiskAssessmentModel  # noqa: F401
from app.seed.init_demo_data import seed_pilot_locations, seed_sources

client = TestClient(app)


@pytest.fixture(autouse=True)
def _e2e_db(tmp_path: Path) -> Generator[None, None, None]:
    """Provide an isolated SQLite DB seeded with pilot locations and sources."""
    db_url = f"sqlite:///{tmp_path / 'e2e_workflow.db'}"
    engine = create_db_engine(db_url)
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory(engine)

    with factory() as seed_db:
        seed_pilot_locations(seed_db)
        seed_sources(seed_db)
        seed_db.commit()

    def _override_get_db() -> Generator:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    from app.api.routes import alerts as alerts_routes
    from app.api.routes import observations as obs_routes
    from app.api.routes import risk as risk_routes
    from app.api.routes import warnings as warn_routes

    app.dependency_overrides[obs_routes._get_db] = _override_get_db
    app.dependency_overrides[risk_routes._get_db] = _override_get_db
    app.dependency_overrides[alerts_routes._get_db] = _override_get_db
    app.dependency_overrides[warn_routes._get_db] = _override_get_db

    yield
    app.dependency_overrides.clear()


def _operator_headers() -> dict[str, str]:
    token = create_access_token("Admin", "admin")
    return {"Authorization": f"Bearer {token}"}


def test_end_to_end_observation_to_alert_action_workflow() -> None:
    headers = _operator_headers()
    location_id = "JK-SGR-01"
    now = datetime.now(UTC)

    # 1. Submit flood observations (rainfall + river gauge)
    rain_resp = client.post(
        "/observations",
        headers=headers,
        json={
            "location_id": location_id,
            "hazard_type": "flood",
            "metric": "rain_mm",
            "value": 64.0,
            "unit": "mm",
            "observed_at": (now - timedelta(minutes=15)).isoformat(),
        },
    )
    assert rain_resp.status_code == 201, rain_resp.text
    rain_obs = rain_resp.json()
    assert rain_obs["location_id"] == location_id
    assert rain_obs["metric"] == "rain_mm"

    gauge_resp = client.post(
        "/observations",
        headers=headers,
        json={
            "location_id": location_id,
            "hazard_type": "flood",
            "metric": "river_level_m",
            "value": 5.6,
            "unit": "m",
            "observed_at": (now - timedelta(minutes=5)).isoformat(),
        },
    )
    assert gauge_resp.status_code == 201, gauge_resp.text

    # Verify persisted observation retrieval
    list_resp = client.get(f"/observations?location_id={location_id}", headers=headers)
    assert list_resp.status_code == 200
    obs_data = list_resp.json()
    assert obs_data["total"] >= 2
    assert any(item["observation_id"] == rain_obs["observation_id"] for item in obs_data["items"])

    # 2. Controlled assessment workflow -> extracts features, checks readiness, executes & saves
    eval_resp = client.post(f"/risk/evaluate/{location_id}", headers=headers)
    assert eval_resp.status_code == 200, eval_resp.text
    eval_data = eval_resp.json()
    assert eval_data["location_id"] == location_id
    assert eval_data["risk_state"]["flood"] is not None
    assert eval_data["risk_state"]["flood"]["prediction_status"] in {"ready", "stale"}

    # Verify persisted assessment via GET /risk/state & GET /risk/current
    state_resp = client.get(f"/risk/state/{location_id}", headers=headers)
    assert state_resp.status_code == 200
    assert state_resp.json()["flood"]["risk_id"] == eval_data["risk_state"]["flood"]["risk_id"]

    current_resp = client.get(f"/risk/current/{location_id}", headers=headers)
    assert current_resp.status_code == 200
    assert current_resp.json()["flood"] is not None

    # 3. Verify spatial exposure analysis (population, infrastructure, critical assets)
    exp_resp = client.get(f"/risk/exposure/{location_id}", headers=headers)
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert exp_data["location_id"] == location_id
    assert exp_data["population_exposed"] > 0
    assert exp_data["roads_exposed_km"] > 0
    assert exp_data["critical_facilities_count"] > 0

    # 4. Verify explainable risk prioritization
    prio_resp = client.get(f"/risk/priority/{location_id}", headers=headers)
    assert prio_resp.status_code == 200
    prio_data = prio_resp.json()
    assert prio_data["location_id"] == location_id
    assert prio_data["priority_level"] in {"MEDIUM", "HIGH", "CRITICAL"}
    assert len(prio_data["explanation"]) >= 3
    assert any("Hazard" in line for line in prio_data["explanation"])
    assert any("Exposure" in line for line in prio_data["explanation"])
    assert any("Readiness & Quality" in line for line in prio_data["explanation"])

    # 5. Verify persisted alert & action history
    alerts_resp = client.get(f"/alerts?location_id={location_id}", headers=headers)
    assert alerts_resp.status_code == 200
    alerts_data = alerts_resp.json()
    assert alerts_data["total"] >= 1
    alert = alerts_data["items"][0]
    alert_id = alert["alert_id"]
    assert alert["is_official_warning"] is False
    assert alert["status"] == "active"

    ack_resp = client.post(
        f"/alerts/{alert_id}/acknowledge",
        headers=headers,
        json={"note": "DDMA control room notified."},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acknowledged"
    assert ack_resp.json()["acknowledged_by"] == "Admin"

    action_resp = client.patch(
        f"/alerts/{alert_id}/action",
        headers=headers,
        json={"status": "in_progress", "action_note": "SDRF team deployed to Jhelum Bund."},
    )
    assert action_resp.status_code == 200
    assert action_resp.json()["status"] == "in_progress"
    assert action_resp.json()["action_note"] == "SDRF team deployed to Jhelum Bund."

    # 6. Verify official warnings remain strictly separate
    warnings_resp = client.get("/warnings", headers=headers)
    assert warnings_resp.status_code == 200
    for w in warnings_resp.json()["items"]:
        assert w["is_read_only"] is True
        assert w["warning_id"] != alert_id


def test_assess_endpoint_unified_with_evaluate_and_unsupported_no_alerts(tmp_path: Path) -> None:
    """Verify /risk/assess matches /risk/evaluate and unsupported predictions create no alerts."""
    from app.repositories.alert_repository import AlertRepository
    from app.repositories.risk_repository import RiskAssessmentRepository
    from app.schemas.common import (
        FreshnessStatus,
        HazardType,
        PredictionStatus,
        ProvenanceMeta,
        RiskClass,
    )
    from app.schemas.exposure import ExposureCoverageStatus, PriorityAssessment
    from app.schemas.risk import RiskAssessmentContract
    from app.services.alert_service import AlertService
    from app.services.risk_orchestrator import RiskOrchestrator

    headers = _operator_headers()

    # Empty state must default to UNSUPPORTED, never LOW
    engine = create_db_engine(f"sqlite:///{tmp_path / 'unit_check.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = get_session_factory(engine)
    with session_factory() as db:
        orch = RiskOrchestrator(RiskAssessmentRepository(db))
        empty_state = orch.get_location_risk_state("JK-DRS-01")
        assert empty_state.highest_risk_class == RiskClass.UNSUPPORTED

        # Unsupported prediction must never create an alert even with elevated priority_level
        now = datetime.now(UTC)
        unsupported_assessment = RiskAssessmentContract(
            risk_id="risk-unsupported-test",
            location_id="JK-DRS-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.UNSUPPORTED,
            score=None,
            confidence=0.0,
            lead_time_hours=12,
            freshness=FreshnessStatus.UNKNOWN,
            prediction_status=PredictionStatus.UNSUPPORTED,
            readiness_reason="Missing snowpack telemetry",
            assessed_at=now,
            provenance=ProvenanceMeta(
                source_id="src-dgre-01",
                source_name="DGRE",
                licence="GODL",
                is_demo_fixture=False,
                ingested_at=now,
            ),
        )
        misleading_priority = PriorityAssessment(
            location_id="JK-DRS-01",
            evaluated_at=now,
            hazard_score=None,
            hazard_risk_class=RiskClass.UNSUPPORTED,
            exposure_score=0.8,
            impact_score=0.8,
            priority_score=0.4,
            coverage_status=ExposureCoverageStatus.COMPLETE,
            priority_level="HIGH",
            confidence=0.0,
            freshness=FreshnessStatus.UNKNOWN,
            prediction_status=PredictionStatus.UNSUPPORTED,
            weights_used={"hazard_weight": 0.5, "impact_weight": 0.5},
            breakdown={"hazard_effective": 0.0, "impact_total": 0.8},
        )
        alert_service = AlertService(AlertRepository(db))
        assert (
            alert_service.generate_for_assessment(unsupported_assessment, misleading_priority)
            is None
        )

    # /risk/assess/{location_id} runs the unified evaluation pipeline
    assess_resp = client.post("/risk/assess/JK-DRS-01", headers=headers)
    assert assess_resp.status_code == 200
    assess_data = assess_resp.json()
    assert assess_data["location_id"] == "JK-DRS-01"
    assert assess_data["risk_state"]["highest_risk_class"] == "unsupported"
    assert assess_data["alert"] is None
