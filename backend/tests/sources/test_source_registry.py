"""Tests for source registry: schemas, freshness, service, and API."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.main import app
from app.models.source import SourceModel
from app.schemas.common import FreshnessStatus
from app.schemas.source import (
    AccessMode,
    SourceContract,
    TrustClassification,
    compute_freshness,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_sources_table() -> None:
    """Ensure tests run against a clean sources table."""
    engine = create_db_engine()
    Base.metadata.create_all(bind=engine)
    factory = get_session_factory(engine)
    with factory() as db:
        db.execute(delete(SourceModel))
        db.commit()


# ── Schema contract tests ────────────────────────────────────────────


def _valid_source_payload(**overrides: object) -> dict:
    """Return a valid SourceContract payload dict."""
    base: dict = {
        "source_id": "imd-aws-demo",
        "provider": "India Meteorological Department",
        "dataset": "AWS Hourly Surface Obs",
        "source_type": "weather",
        "access_mode": "sample",
        "licence": "Government Open Data Licence – India",
        "reference_url": "https://mausam.imd.gov.in/",
        "update_frequency_minutes": 60,
        "trust_classification": "institutional",
        "is_authoritative": False,
        "is_demo_fixture": True,
    }
    base.update(overrides)
    return base


class TestSourceContract:
    """Pydantic validation for SourceContract."""

    def test_valid_payload(self) -> None:
        sc = SourceContract(**_valid_source_payload())
        assert sc.source_id == "imd-aws-demo"
        assert sc.access_mode == AccessMode.SAMPLE
        assert sc.trust_classification == TrustClassification.INSTITUTIONAL

    def test_missing_provider_rejected(self) -> None:
        data = _valid_source_payload()
        del data["provider"]
        with pytest.raises(Exception):
            SourceContract(**data)

    def test_invalid_access_mode_rejected(self) -> None:
        with pytest.raises(Exception):
            SourceContract(**_valid_source_payload(access_mode="realtime"))

    def test_invalid_source_type_rejected(self) -> None:
        with pytest.raises(Exception):
            SourceContract(**_valid_source_payload(source_type="satellite"))

    def test_update_frequency_bounds(self) -> None:
        with pytest.raises(Exception):
            SourceContract(**_valid_source_payload(update_frequency_minutes=0))
        with pytest.raises(Exception):
            SourceContract(
                **_valid_source_payload(update_frequency_minutes=99999)
            )

    def test_access_modes_distinct(self) -> None:
        modes = {m.value for m in AccessMode}
        assert modes == {"live", "cached", "sample"}


# ── Freshness logic tests ────────────────────────────────────────────


class TestComputeFreshness:
    """Deterministic freshness status from cadence and last-fetch time."""

    def test_never_fetched_is_unknown(self) -> None:
        assert compute_freshness(60, None) == FreshnessStatus.UNKNOWN

    def test_within_threshold_is_fresh(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        last = now - timedelta(minutes=80)  # 80 < 90 (60 * 1.5)
        assert compute_freshness(60, last, now=now) == FreshnessStatus.FRESH

    def test_beyond_threshold_is_stale(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        last = now - timedelta(minutes=100)  # 100 > 90
        assert compute_freshness(60, last, now=now) == FreshnessStatus.STALE

    def test_exact_boundary_is_fresh(self) -> None:
        now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        last = now - timedelta(minutes=90)  # exactly 1.5×
        assert compute_freshness(60, last, now=now) == FreshnessStatus.FRESH


# ── API integration tests ────────────────────────────────────────────


def _admin_headers() -> dict[str, str]:
    """Log in as admin and return Authorization header."""
    resp = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestSourceAPI:
    """HTTP-level tests for the /sources endpoints."""

    def test_list_sources_requires_auth(self) -> None:
        assert client.get("/sources").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/sources/imd-aws-demo").status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_sources_empty(self) -> None:
        resp = client.get("/sources", headers=_admin_headers())
        assert resp.status_code == status.HTTP_200_OK
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_register_and_retrieve(self) -> None:
        headers = _admin_headers()
        payload = _valid_source_payload(source_id="test-register-01")
        resp = client.post("/sources", json=payload, headers=headers)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["source_id"] == "test-register-01"
        assert data["access_mode"] == "sample"
        assert data["trust_classification"] == "institutional"
        assert data["licence"] == payload["licence"]
        assert data["freshness"] == "unknown"  # never fetched

        # Retrieve by ID
        resp2 = client.get("/sources/test-register-01", headers=headers)
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.json()["provider"] == payload["provider"]

    def test_unknown_source_returns_404(self) -> None:
        resp = client.get("/sources/does-not-exist", headers=_admin_headers())
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_register_requires_admin(self) -> None:
        payload = _valid_source_payload(source_id="unauth-01")
        resp = client.post("/sources", json=payload)
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_filter_by_source_type(self) -> None:
        headers = _admin_headers()
        payload = _valid_source_payload(
            source_id="hydro-filter-01", source_type="hydrology"
        )
        client.post("/sources", json=payload, headers=headers)
        resp = client.get("/sources", params={"source_type": "hydrology"}, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        ids = [s["source_id"] for s in resp.json()["items"]]
        assert "hydro-filter-01" in ids

    def test_filter_by_access_mode(self) -> None:
        headers = _admin_headers()
        payload = _valid_source_payload(
            source_id="cached-filter-01", access_mode="cached"
        )
        client.post("/sources", json=payload, headers=headers)
        resp = client.get("/sources", params={"access_mode": "cached"}, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        ids = [s["source_id"] for s in resp.json()["items"]]
        assert "cached-filter-01" in ids

    def test_record_fetch_updates_freshness(self) -> None:
        headers = _admin_headers()
        payload = _valid_source_payload(source_id="fetch-unique-test-01")
        reg_resp = client.post("/sources", json=payload, headers=headers)
        assert reg_resp.status_code == status.HTTP_201_CREATED

        r1 = client.get("/sources/fetch-unique-test-01", headers=headers)
        assert r1.status_code == status.HTTP_200_OK
        assert r1.json()["freshness"] == "unknown"

        r2 = client.post("/sources/fetch-unique-test-01/fetch", headers=headers)
        assert r2.status_code == status.HTTP_200_OK
        assert r2.json()["freshness"] == "fresh"
        assert r2.json()["last_fetched_at"] is not None

    def test_record_fetch_unknown_source_404(self) -> None:
        headers = _admin_headers()
        resp = client.post("/sources/no-such-source/fetch", headers=headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_provenance_fields_round_trip(self) -> None:
        headers = _admin_headers()
        payload = _valid_source_payload(
            source_id="prov-round-01",
            licence="CC-BY-4.0",
            reference_url="https://example.org/data",
            is_demo_fixture=True,
        )
        client.post("/sources", json=payload, headers=headers)
        resp = client.get("/sources/prov-round-01", headers=headers)
        data = resp.json()
        assert data["licence"] == "CC-BY-4.0"
        assert data["reference_url"] == "https://example.org/data"
        assert data["is_demo_fixture"] is True
