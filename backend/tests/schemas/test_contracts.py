"""Validation and OpenAPI schema generation tests for domain contracts."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.openapi.utils import get_openapi
from pydantic import ValidationError
from pydantic.json_schema import models_json_schema

from app.core.errors import ErrorDetail, ErrorEnvelope, build_error_envelope
from app.main import app
from app.schemas.common import (
    FreshnessStatus,
    HazardType,
    PredictionStatus,
    ProvenanceMeta,
    RiskClass,
)
from app.schemas.location import LocationOut
from app.schemas.observation import ObservationContract, ObservationMetric
from app.schemas.risk import RiskAssessmentContract
from app.schemas.source import SourceContract, SourceType
from app.schemas.warning import OfficialWarningContract, WarningAuthority

NOW = datetime(2026, 11, 25, 0, 0, tzinfo=UTC)


def _sample_provenance() -> ProvenanceMeta:
    return ProvenanceMeta(
        source_id="src-demo-imd",
        source_name="IMD Demo Cache",
        licence="CC-BY-4.0-demo",
        is_demo_fixture=True,
        ingested_at=NOW,
    )


def test_valid_contracts_and_error_envelope() -> None:
    src = SourceContract(
        source_id="src-demo-imd",
        source_name="IMD Demo Cache",
        source_type=SourceType.WEATHER,
        licence="CC-BY-4.0-demo",
        update_frequency_minutes=60,
    )
    obs = ObservationContract(
        observation_id="obs-1",
        location_id="JK-SGR-01",
        source_id=src.source_id,
        observed_at=NOW,
        metric=ObservationMetric.RAIN_MM,
        value=18.4,
        unit="mm",
    )
    risk = RiskAssessmentContract(
        risk_id="risk-1",
        location_id="JK-SGR-01",
        hazard_type=HazardType.FLOOD,
        risk_class=RiskClass.MODERATE,
        score=0.55,
        confidence=0.78,
        lead_time_hours=6,
        freshness=FreshnessStatus.FRESH,
        prediction_status=PredictionStatus.INDICATIVE,
        assessed_at=NOW,
        provenance=_sample_provenance(),
    )
    warn = OfficialWarningContract(
        warning_id="warn-cwc-1",
        authority=WarningAuthority.CWC,
        hazard_type=HazardType.FLOOD,
        location_id="JK-SGR-01",
        severity_label="Watch",
        headline="Jhelum water level rising near Sangam",
        issued_at=NOW,
        valid_until=NOW + timedelta(hours=12),
        provenance="official:cwc-bulletin-demo",
    )
    err = build_error_envelope(
        "VALIDATION_ERROR",
        "Invalid payload",
        [ErrorDetail(field="unit", code="INVALID_UNIT", message="Expected mm")],
    )
    assert obs.unit == "mm"
    assert risk.prediction_status == PredictionStatus.INDICATIVE
    assert warn.is_read_only is True
    assert err.error_code == "VALIDATION_ERROR"


def test_missing_fields_and_invalid_enum_rejected() -> None:
    with pytest.raises(ValidationError):
        SourceContract(
            source_id="s1",
            source_name="Bad",
            source_type="earthquake",  # type: ignore[arg-type]
            licence="MIT",
            update_frequency_minutes=15,
        )

    with pytest.raises(ValidationError):
        ObservationContract(observation_id="obs-2", location_id="JK-SGR-01")  # type: ignore[call-arg]


def test_invalid_unit_rejected() -> None:
    with pytest.raises(ValidationError, match="Invalid unit"):
        ObservationContract(
            observation_id="obs-3",
            location_id="JK-SGR-01",
            source_id="src-1",
            observed_at=NOW,
            metric=ObservationMetric.RAIN_MM,
            value=10.0,
            unit="cm",
        )


def test_naive_timestamp_rejected() -> None:
    naive = datetime(2026, 11, 25, 0, 0)
    with pytest.raises(ValidationError, match="timezone-aware"):
        ObservationContract(
            observation_id="obs-4",
            location_id="JK-SGR-01",
            source_id="src-1",
            observed_at=naive,
            metric=ObservationMetric.TEMP_C,
            value=2.5,
            unit="C",
        )


def test_unsupported_prediction_status_rules() -> None:
    unsupported = RiskAssessmentContract(
        risk_id="risk-unsupported",
        location_id="JK-DRS-01",
        hazard_type=HazardType.AVALANCHE,
        risk_class=RiskClass.UNSUPPORTED,
        score=None,
        confidence=0.0,
        lead_time_hours=0,
        freshness=FreshnessStatus.UNKNOWN,
        prediction_status=PredictionStatus.UNSUPPORTED,
        readiness_reason="Insufficient snowpack labels.",
        assessed_at=NOW,
        provenance=_sample_provenance(),
    )
    assert unsupported.score is None

    with pytest.raises(ValidationError, match="score must be None"):
        RiskAssessmentContract(
            risk_id="risk-bad",
            location_id="JK-DRS-01",
            hazard_type=HazardType.AVALANCHE,
            risk_class=RiskClass.UNSUPPORTED,
            score=0.4,
            confidence=0.2,
            lead_time_hours=6,
            freshness=FreshnessStatus.UNKNOWN,
            prediction_status=PredictionStatus.UNSUPPORTED,
            assessed_at=NOW,
            provenance=_sample_provenance(),
        )


def test_openapi_schema_generation_succeeds() -> None:
    _, top_schema = models_json_schema(
        [
            (LocationOut, "validation"),
            (SourceContract, "validation"),
            (ObservationContract, "validation"),
            (RiskAssessmentContract, "validation"),
            (OfficialWarningContract, "validation"),
            (ErrorEnvelope, "validation"),
        ]
    )
    assert "$defs" in top_schema
    openapi = get_openapi(title=app.title, version=app.version, routes=app.routes)
    assert "paths" in openapi
