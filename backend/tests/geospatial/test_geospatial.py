"""Tests for geospatial module: CRS, geometry repair, layer loading, and spatial joins."""

from pathlib import Path

import pytest
from shapely.geometry import Point, Polygon

from app.geospatial.crs import (
    CRSError,
    epsg3857_to_epsg4326_coords,
    epsg4326_to_epsg3857_coords,
    parse_crs,
    transform_geometry,
)
from app.geospatial.geometry import validate_and_repair_geometry
from app.geospatial.layer_loader import load_geojson_layer
from app.geospatial.spatial_join import (
    haversine_distance_km,
    match_observation_to_location,
)
from app.models.location import LocationRecord
from app.repositories.location_repository import LocationRepository
from app.services.geospatial_service import GeospatialService

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_PATH = REPO_ROOT / "data" / "layers" / "pilot_coverage_zones.geojson"


@pytest.fixture
def sample_locations() -> list[LocationRecord]:
    return [
        LocationRecord(
            location_id="JK-SGR-01",
            name="Srinagar",
            admin_unit="Srinagar, J&K",
            latitude=34.0837,
            longitude=74.7973,
            supported_hazards=["flood"],
            coverage_status="supported",
            coverage_note="Pilot flood monitoring hub",
        ),
        LocationRecord(
            location_id="UK-JSH-01",
            name="Joshimath",
            admin_unit="Chamoli, Uttarakhand",
            latitude=30.5574,
            longitude=79.5663,
            supported_hazards=["flood", "avalanche"],
            coverage_status="supported",
            coverage_note="Upper Alaknanda monitoring hub",
        ),
        LocationRecord(
            location_id="LA-DRS-01",
            name="Drass",
            admin_unit="Kargil, Ladakh",
            latitude=34.4295,
            longitude=75.7601,
            supported_hazards=["avalanche"],
            coverage_status="supported",
            coverage_note="Zojila avalanche corridor monitoring",
        ),
    ]


class TestCRS:
    def test_parse_crs(self) -> None:
        assert parse_crs(None) == 4326
        assert parse_crs(4326) == 4326
        assert parse_crs("EPSG:4326") == 4326
        assert parse_crs("EPSG:3857") == 3857
        assert parse_crs("urn:ogc:def:crs:EPSG::4326") == 4326
        assert parse_crs({"type": "name", "properties": {"name": "EPSG:3857"}}) == 3857

        with pytest.raises(CRSError):
            parse_crs("EPSG:9999")

    def test_crs_round_trip(self) -> None:
        lon, lat = 74.7973, 34.0837
        x, y = epsg4326_to_epsg3857_coords(lon, lat)
        lon_back, lat_back = epsg3857_to_epsg4326_coords(x, y)
        assert lon_back == pytest.approx(lon, abs=1e-5)
        assert lat_back == pytest.approx(lat, abs=1e-5)

    def test_transform_geometry(self) -> None:
        pt_wgs = Point(75.76, 34.43)
        pt_merc = transform_geometry(pt_wgs, from_epsg=4326, to_epsg=3857)
        assert pt_merc.x > 1000000
        pt_restored = transform_geometry(pt_merc, from_epsg=3857, to_epsg=4326)
        assert pt_restored.x == pytest.approx(pt_wgs.x, abs=1e-4)
        assert pt_restored.y == pytest.approx(pt_wgs.y, abs=1e-4)


class TestGeometryValidationAndRepair:
    def test_valid_geometry(self) -> None:
        poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
        res = validate_and_repair_geometry(poly)
        assert res.is_valid is True
        assert res.repaired is False
        assert res.method == "as_is"

    def test_invalid_bowtie_polygon_repair(self) -> None:
        # Self-intersecting figure-8 / bowtie polygon
        bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
        assert not bowtie.is_valid

        res = validate_and_repair_geometry(bowtie, allow_repair=True)
        assert res.is_valid is True
        assert res.repaired is True
        assert res.method in ("make_valid", "buffer_zero")
        assert res.geometry is not None
        assert res.geometry.is_valid

    def test_empty_or_broken_geometry_rejected(self) -> None:
        res = validate_and_repair_geometry(Polygon())
        assert res.is_valid is False
        assert res.method == "rejected"

        res2 = validate_and_repair_geometry({"type": "Polygon", "coordinates": []})
        assert res2.is_valid is False
        assert res2.method == "rejected"


class TestLayerLoader:
    def test_load_pilot_coverage_zones_geojson(self) -> None:
        assert FIXTURE_PATH.exists()
        loaded = load_geojson_layer(FIXTURE_PATH, layer_id="pilot_zones")

        assert loaded.metadata.layer_id == "pilot_zones"
        assert loaded.metadata.feature_count == 3
        assert loaded.metadata.target_crs_epsg == 4326
        assert loaded.metadata.bounds is not None
        assert len(loaded.features) == 3

        ids = [f.properties.get("location_id") for f in loaded.features]
        assert "JK-SGR-01" in ids
        assert "UK-JSH-01" in ids
        assert "LA-DRS-01" in ids

    def test_load_layer_with_mercator_crs_normalizes_to_wgs84(self) -> None:
        # Create a sample geojson in EPSG:3857
        x, y = epsg4326_to_epsg3857_coords(74.8, 34.1)
        geojson_3857 = {
            "type": "FeatureCollection",
            "crs": {"type": "name", "properties": {"name": "EPSG:3857"}},
            "features": [
                {
                    "type": "Feature",
                    "id": 1,
                    "properties": {"name": "Test Point"},
                    "geometry": {"type": "Point", "coordinates": [x, y]},
                }
            ],
        }
        loaded = load_geojson_layer(geojson_3857, layer_id="mercator_layer")
        assert loaded.metadata.source_crs_epsg == 3857
        assert loaded.metadata.target_crs_epsg == 4326
        feat = loaded.features[0]
        assert feat.geometry.x == pytest.approx(74.8, abs=1e-3)
        assert feat.geometry.y == pytest.approx(34.1, abs=1e-3)


class TestSpatialJoin:
    def test_haversine_distance(self) -> None:
        # Distance between Srinagar and Drass (~100-115 km)
        d = haversine_distance_km(34.0837, 74.7973, 34.4295, 75.7601)
        assert 90.0 < d < 120.0

    def test_spatial_join_match_closest(self, sample_locations: list[LocationRecord]) -> None:
        # Coordinate 5 km from Srinagar center
        match = match_observation_to_location(
            lat=34.10,
            lon=74.82,
            locations=sample_locations,
            observation_id="obs-01",
            max_distance_km=25.0,
        )
        assert match.is_assigned is True
        assert match.location_id == "JK-SGR-01"
        assert match.status == "assigned"
        assert match.distance_km is not None
        assert match.distance_km < 10.0

    def test_spatial_join_out_of_coverage(self, sample_locations: list[LocationRecord]) -> None:
        # Coordinate in New Delhi (~314 km from Joshimath)
        match = match_observation_to_location(
            lat=28.6139,
            lon=77.2090,
            locations=sample_locations,
            observation_id="obs-far",
            max_distance_km=50.0,
        )
        assert match.is_assigned is False
        assert match.location_id is None
        assert match.status == "out_of_coverage"
        assert match.distance_km is not None
        assert match.distance_km > 200.0

    def test_spatial_join_with_coverage_polygons(
        self, sample_locations: list[LocationRecord]
    ) -> None:
        loaded = load_geojson_layer(FIXTURE_PATH, layer_id="pilot_zones")
        zones = {f.properties["location_id"]: f.geometry for f in loaded.features}

        # Point inside Drass polygon
        match = match_observation_to_location(
            lat=34.45,
            lon=75.75,
            locations=sample_locations,
            coverage_zones=zones,
        )
        assert match.is_assigned is True
        assert match.location_id == "LA-DRS-01"
        assert "Contained in polygon coverage zone" in match.details


class TestGeospatialService:
    def test_service_layer_management_and_matching(
        self, sample_locations: list[LocationRecord]
    ) -> None:
        repo = LocationRepository()
        for loc in sample_locations:
            repo.upsert(loc)

        svc = GeospatialService(location_repo=repo)
        layer = svc.load_and_register_geojson(FIXTURE_PATH, layer_id="coverage_zones")
        assert layer.metadata.feature_count == 3

        listed = svc.list_layers()
        assert len(listed) == 1
        assert listed[0]["layer_id"] == "coverage_zones"

        # Point matching through service
        match = svc.match_point(lat=30.56, lon=79.57)
        assert match.is_assigned is True
        assert match.location_id == "UK-JSH-01"

        # Batch matching
        pts = [
            {"lat": 34.09, "lon": 74.80, "id": "p1"},
            {"lat": 12.97, "lon": 77.59, "id": "p_bengaluru"},
        ]
        results = svc.match_points_batch(pts)
        assert len(results) == 2
        assert results[0].is_assigned is True
        assert results[0].location_id == "JK-SGR-01"
        assert results[1].is_assigned is False
        assert results[1].status == "out_of_coverage"
