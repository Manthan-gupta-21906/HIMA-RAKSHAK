"""Spatial joins between observation coordinates and pilot locations/coverage zones."""

import math
from dataclasses import dataclass
from typing import Any

from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from app.models.location import LocationRecord


@dataclass
class SpatialJoinMatch:
    """Result of matching an observation to a pilot location."""

    observation_id: str | None
    location_id: str | None
    location_name: str | None
    distance_km: float | None
    is_assigned: bool
    status: str  # "assigned", "out_of_coverage", "no_locations"
    details: str = ""


# Earth radius in kilometers for haversine distance
EARTH_RADIUS_KM = 6371.0
DEFAULT_MAX_DISTANCE_KM = 25.0


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two geographic coordinates in kilometers."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def match_observation_to_location(
    lat: float,
    lon: float,
    locations: list[LocationRecord],
    *,
    observation_id: str | None = None,
    max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    coverage_zones: dict[str, BaseGeometry] | None = None,
) -> SpatialJoinMatch:
    """Assign an observation coordinate (lat, lon) to the nearest pilot location.

    If coverage_zones (Polygons in EPSG:4326) are provided, first tests point containment.
    Otherwise, matches to the nearest location within `max_distance_km`.
    Coordinates outside `max_distance_km` remain unassigned.
    """
    if not locations:
        return SpatialJoinMatch(
            observation_id=observation_id,
            location_id=None,
            location_name=None,
            distance_km=None,
            is_assigned=False,
            status="no_locations",
            details="No pilot locations available to match against",
        )

    pt = Point(lon, lat)

    # 1. Polygon containment check if coverage zones supplied
    if coverage_zones:
        for loc_id, poly in coverage_zones.items():
            if poly.contains(pt):
                matched_rec = next((loc for loc in locations if loc.location_id == loc_id), None)
                if matched_rec:
                    dist = haversine_distance_km(
                        lat, lon, matched_rec.latitude, matched_rec.longitude
                    )
                    return SpatialJoinMatch(
                        observation_id=observation_id,
                        location_id=matched_rec.location_id,
                        location_name=matched_rec.name,
                        distance_km=round(dist, 3),
                        is_assigned=True,
                        status="assigned",
                        details=f"Contained in polygon coverage zone for {matched_rec.location_id}",
                    )

    # 2. Distance-based spatial join (nearest neighbor within max_distance_km)
    closest_loc: LocationRecord | None = None
    min_dist = float("inf")

    for loc in locations:
        dist = haversine_distance_km(lat, lon, loc.latitude, loc.longitude)
        if dist < min_dist:
            min_dist = dist
            closest_loc = loc

    if closest_loc is not None and min_dist <= max_distance_km:
        return SpatialJoinMatch(
            observation_id=observation_id,
            location_id=closest_loc.location_id,
            location_name=closest_loc.name,
            distance_km=round(min_dist, 3),
            is_assigned=True,
            status="assigned",
            details=(
                f"Matched to {closest_loc.location_id} ({min_dist:.2f} km <= {max_distance_km} km)"
            ),
        )

    return SpatialJoinMatch(
        observation_id=observation_id,
        location_id=None,
        location_name=None,
        distance_km=round(min_dist, 3) if closest_loc is not None else None,
        is_assigned=False,
        status="out_of_coverage",
        details=(
            f"Nearest location was {min_dist:.2f} km away, exceeding max threshold"
            f" {max_distance_km} km"
        ),
    )


def batch_spatial_join(
    points: list[dict[str, Any]],  # [{"lat": float, "lon": float, "id": str, ...}]
    locations: list[LocationRecord],
    *,
    max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    coverage_zones: dict[str, BaseGeometry] | None = None,
) -> list[SpatialJoinMatch]:
    """Perform spatial join on a batch of points."""
    return [
        match_observation_to_location(
            lat=p["lat"],
            lon=p["lon"],
            locations=locations,
            observation_id=p.get("id"),
            max_distance_km=max_distance_km,
            coverage_zones=coverage_zones,
        )
        for p in points
    ]
