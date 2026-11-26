"""API tests for the pilot location catalogue with pagination and role policy."""

from fastapi.testclient import TestClient

from app.core.security import create_access_token
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
    assert "pagination" in data
    assert data["pagination"]["page"] == 1


def test_list_locations_pagination() -> None:
    res = client.get("/locations", params={"page": 1, "page_size": 2})
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 2
    assert data["pagination"]["has_next"] is True


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
    assert missing.json()["error_code"] == "HTTP_404"


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

    # Forged X-User-Role header without JWT must be rejected
    forged = client.post("/locations", json=payload, headers={"X-User-Role": "admin"})
    assert forged.status_code == 401

    # Invalid Bearer token must be rejected
    invalid = client.post(
        "/locations", json=payload, headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert invalid.status_code == 401

    # Viewer and operator tokens get 403 on admin-only write
    viewer_token = create_access_token("viewer_user", "viewer")
    assert (
        client.post(
            "/locations", json=payload, headers={"Authorization": f"Bearer {viewer_token}"}
        ).status_code
        == 403
    )
    operator_token = create_access_token("operator_user", "district_operator")
    assert (
        client.post(
            "/locations", json=payload, headers={"Authorization": f"Bearer {operator_token}"}
        ).status_code
        == 403
    )

    # Admin JWT succeeds
    admin_token = create_access_token("admin_user", "admin")
    created = client.post(
        "/locations", json=payload, headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert created.status_code == 201
    assert created.json()["location_id"] == "JK-PAH-01"

    # Test patch coverage with Bearer JWT token
    patch_payload = {
        "coverage_status": "supported",
        "coverage_note": "Upgraded with field telemetry station.",
    }
    patched = client.patch(
        "/locations/JK-PAH-01/coverage",
        json=patch_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patched.status_code == 200
    assert patched.json()["coverage_status"] == "supported"

    # Viewer token gets 403 on protected write
    denied = client.patch(
        "/locations/JK-PAH-01/coverage",
        json=patch_payload,
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert denied.status_code == 403
