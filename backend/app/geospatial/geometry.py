"""Geometry validation, repair, and normalization utilities."""

import logging
from dataclasses import dataclass
from typing import Any

from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity, make_valid

logger = logging.getLogger(__name__)


@dataclass
class GeometryValidationResult:
    """Outcome of validating and optionally repairing a geometry."""

    is_valid: bool
    repaired: bool
    method: str  # "as_is", "make_valid", "buffer_zero", "rejected"
    details: str
    geometry: BaseGeometry | None = None
    geojson: dict[str, Any] | None = None


def validate_and_repair_geometry(
    raw_geom: BaseGeometry | dict[str, Any],
    *,
    allow_repair: bool = True,
) -> GeometryValidationResult:
    """Validate a Shapely geometry or GeoJSON mapping and repair if needed.

    If valid, returns method='as_is'.
    If invalid and allow_repair=True, attempts shapely.validation.make_valid
    or buffer(0). If successful, returns repaired=True with the method logged.
    If unrepairable or allow_repair=False, returns is_valid=False, geometry=None.
    """
    try:
        geom = shape(raw_geom) if isinstance(raw_geom, dict) else raw_geom
    except Exception as exc:
        return GeometryValidationResult(
            is_valid=False,
            repaired=False,
            method="rejected",
            details=f"Invalid geometry structure: {exc}",
            geometry=None,
            geojson=None,
        )

    if geom.is_empty:
        return GeometryValidationResult(
            is_valid=False,
            repaired=False,
            method="rejected",
            details="Geometry is empty",
            geometry=None,
            geojson=None,
        )

    if geom.is_valid:
        return GeometryValidationResult(
            is_valid=True,
            repaired=False,
            method="as_is",
            details="Geometry is valid",
            geometry=geom,
            geojson=mapping(geom),
        )

    reason = explain_validity(geom)
    if not allow_repair:
        return GeometryValidationResult(
            is_valid=False,
            repaired=False,
            method="rejected",
            details=f"Geometry invalid and repair disabled: {reason}",
            geometry=None,
            geojson=None,
        )

    # Attempt 1: make_valid
    try:
        repaired_geom = make_valid(geom)
        if repaired_geom.is_valid and not repaired_geom.is_empty:
            logger.info("Geometry repaired using make_valid (was: %s)", reason)
            return GeometryValidationResult(
                is_valid=True,
                repaired=True,
                method="make_valid",
                details=f"Repaired via make_valid (reason was: {reason})",
                geometry=repaired_geom,
                geojson=mapping(repaired_geom),
            )
    except Exception as exc:
        logger.debug("make_valid failed: %s", exc)

    # Attempt 2: buffer(0)
    try:
        repaired_geom = geom.buffer(0)
        if repaired_geom.is_valid and not repaired_geom.is_empty:
            logger.info("Geometry repaired using buffer(0) (was: %s)", reason)
            return GeometryValidationResult(
                is_valid=True,
                repaired=True,
                method="buffer_zero",
                details=f"Repaired via buffer(0) (reason was: {reason})",
                geometry=repaired_geom,
                geojson=mapping(repaired_geom),
            )
    except Exception as exc:
        logger.debug("buffer(0) failed: %s", exc)

    return GeometryValidationResult(
        is_valid=False,
        repaired=False,
        method="rejected",
        details=f"Unable to repair invalid geometry: {reason}",
        geometry=None,
        geojson=None,
    )
