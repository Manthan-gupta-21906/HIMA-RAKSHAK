"""API tests for the pilot location catalogue."""

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.location_repository import LocationRepository
from app.seed.locations import PILOT_LOCATIONS, seed_locations

client = TestClient(app)


def test_list_locations_returns_seeded_demo_fixtures() -> None:
    res = client.get("/locations")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= len(PILOT_LOCATIONS)
    assert all(item["is_demo_fixture"] is True for item in data["items"])


def test_search_locations_by_query_and_hazard() -> None:
    res = client.get("/locations", params={"q": "Srinagar", "hazard_type": "flood"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["location_id"] == "JK-SGR-01"


def test_unsupported_coverage_is_explicit() -> None:
    res = client.get("/locations", params={"coverage_status": "unsupported"})
    assert res.status_code == 200
    items = res.json()["items"]
    assert any(item["location_id"] == "JK-DRS-01" for item in items)
    drass = next(item for item in items if item["location_id"] == "JK-DRS-01")
    assert drass["coverage_status"] == "unsupported"
    assert "Unsupported" in drass["coverage_note"]


def test_get_location_detail_and_unknown_404() -> None:
    ok = client.get("/locations/JK-GUL-01")
    assert ok.status_code == 200
    assert ok.json()["name"].startswith("Gulmarg")

    missing = client.get("/locations/JK-UNKNOWN-99")
    assert missing.status_code == 404


def test_seed_locations_is_repeatable() -> None:
    repo = LocationRepository()
    first = seed_locations(repo)
    second = seed_locations(repo)
    assert first == len(PILOT_LOCATIONS)
    assert second == 0
    assert repo.count() == len(PILOT_LOCATIONS)


def test_protected_writes_enforce_role_policy() -> None:
    payload = {
        "location_id": "JK-PAH-01",
        "name": "Pahalgam — Lidder Valley",
        "admin_unit": "Anantnag District, J&K",
        "latitude": 34.0161,
        "longitude": 75.3150,
        "supported_hazards": ["flood"],
        "coverage_status": "partial",
        "coverage_note": "Added in test.",
    }
    unauth = client.post("/locations", json=payload)
    assert unauth.status_code == 401

    forbidden = client.post(
        "/locations", json=payload, headers={"X-User-Role": "district_team"}
    )
    assert forbidden.status_code == 403

    created = client.post("/locations", json=payload, headers={"X-User-Role": "admin"})
    assert created.status_code == 201
    assert created.json()["location_id"] == "JK-PAH-01"

    patched = client.patch(
        "/locations/JK-PAH-01/coverage",
        json={"coverage_status": "supported", "coverage_note": "Validated locally."},
        headers={"X-User-Role": "admin"},
    )
    assert patched.status_code == 200
    assert patched.json()["coverage_status"] == "supported"
