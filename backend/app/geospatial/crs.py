"""Coordinate Reference System (CRS) definitions, parsing, and transformations."""

import math
from typing import Any

from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

# Project standard CRS is WGS 84 (EPSG:4326)
PROJECT_CRS_EPSG = 4326
PROJECT_CRS_URN = "urn:ogc:def:crs:EPSG::4326"
PROJECT_CRS_NAME = "EPSG:4326"

# Supported input CRS identifiers and their canonical EPSG code
SUPPORTED_CRS_MAP: dict[str, int] = {
    "4326": 4326,
    "epsg:4326": 4326,
    "urn:ogc:def:crs:epsg::4326": 4326,
    "wgs84": 4326,
    "wgs 84": 4326,
    "3857": 3857,
    "epsg:3857": 3857,
    "urn:ogc:def:crs:epsg::3857": 3857,
    "web mercator": 3857,
    "pseudo-mercator": 3857,
}


class CRSError(ValueError):
    """Raised when an unsupported or invalid CRS is encountered."""


def parse_crs(crs_input: Any) -> int:
    """Parse a CRS string, dict, or integer into an EPSG code."""
    if crs_input is None:
        return PROJECT_CRS_EPSG

    if isinstance(crs_input, int):
        if crs_input in (4326, 3857):
            return crs_input
        raise CRSError(f"Unsupported EPSG code: {crs_input}. Supported: [4326, 3857]")

    if isinstance(crs_input, dict):
        props = crs_input.get("properties", {})
        name = props.get("name", "")
        return parse_crs(name)

    if isinstance(crs_input, str):
        cleaned = crs_input.strip().lower()
        if cleaned in SUPPORTED_CRS_MAP:
            return SUPPORTED_CRS_MAP[cleaned]
        if cleaned.startswith("epsg:"):
            code_str = cleaned[5:]
            if code_str.isdigit() and int(code_str) in (4326, 3857):
                return int(code_str)
        raise CRSError(
            f"Unsupported CRS identifier: '{crs_input}'. Supported: EPSG:4326, EPSG:3857"
        )

    raise CRSError(f"Invalid CRS input type: {type(crs_input)}")


def epsg3857_to_epsg4326_coords(x: float, y: float, *args: Any) -> tuple[float, ...]:
    """Transform Spherical/Web Mercator (meters) to WGS84 (lon, lat in degrees)."""
    lon = (x / 20037508.342789244) * 180.0
    lat = (y / 20037508.342789244) * 180.0
    lat = (
        180.0
        / math.pi
        * (2.0 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    )
    # Clamp coordinates to geographic limits
    lon = max(-180.0, min(180.0, lon))
    lat = max(-89.999999, min(89.999999, lat))
    if args:
        return (lon, lat, *args)
    return (lon, lat)


def epsg4326_to_epsg3857_coords(lon: float, lat: float, *args: Any) -> tuple[float, ...]:
    """Transform WGS84 (lon, lat in degrees) to Spherical/Web Mercator (meters)."""
    x = (lon * 20037508.342789244) / 180.0
    clipped_lat = max(-89.9, min(89.9, lat))
    y = (
        math.log(math.tan((90.0 + clipped_lat) * math.pi / 360.0))
        / (math.pi / 180.0)
    )
    y = (y * 20037508.342789244) / 180.0
    if args:
        return (x, y, *args)
    return (x, y)


def transform_geometry(
    geom: BaseGeometry,
    from_epsg: int,
    to_epsg: int = PROJECT_CRS_EPSG,
) -> BaseGeometry:
    """Transform a Shapely geometry from source CRS to destination CRS."""
    if from_epsg == to_epsg:
        return geom

    if from_epsg == 3857 and to_epsg == 4326:
        return transform(epsg3857_to_epsg4326_coords, geom)

    if from_epsg == 4326 and to_epsg == 3857:
        return transform(epsg4326_to_epsg3857_coords, geom)

    raise CRSError(
        f"Direct transformation between EPSG:{from_epsg} and EPSG:{to_epsg} is not supported."
    )
