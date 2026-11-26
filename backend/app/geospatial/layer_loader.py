"""GeoJSON and vector/raster layer metadata loading."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shapely.geometry.base import BaseGeometry

from app.geospatial.crs import PROJECT_CRS_EPSG, parse_crs, transform_geometry
from app.geospatial.geometry import validate_and_repair_geometry


@dataclass
class LayerFeature:
    """Validated feature inside a vector spatial layer."""

    id: str | int | None
    geometry: BaseGeometry
    geojson: dict[str, Any]
    properties: dict[str, Any]
    repaired: bool = False
    repair_method: str = "as_is"


@dataclass
class LayerMetadata:
    """Metadata describing a vector or raster layer."""

    layer_id: str
    name: str
    layer_type: str  # "vector" or "raster"
    source_crs_epsg: int
    target_crs_epsg: int
    feature_count: int
    bounds: tuple[float, float, float, float] | None  # (minx, miny, maxx, maxy) in target CRS
    description: str = ""
    is_demo_fixture: bool = True
    provenance: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedLayer:
    """Complete loaded layer with metadata and normalized features."""

    metadata: LayerMetadata
    features: list[LayerFeature]


def load_geojson_layer(
    source: str | Path | dict[str, Any],
    layer_id: str,
    name: str | None = None,
    description: str = "",
    provenance: str = "demo_fixture",
    is_demo_fixture: bool = True,
    allow_repair: bool = True,
) -> LoadedLayer:
    """Load and normalize a GeoJSON FeatureCollection or geometry dict to EPSG:4326."""
    if isinstance(source, Path):
        data = json.loads(source.read_text(encoding="utf-8"))
    elif isinstance(source, str):
        data = json.loads(source)
    elif isinstance(source, dict):
        data = source
    else:
        raise ValueError(f"Unsupported source type for GeoJSON: {type(source)}")

    source_crs = parse_crs(data.get("crs"))
    raw_features = data.get("features", [])
    if not raw_features and data.get("type") in ("Feature", "Point", "Polygon", "MultiPolygon"):
        if data.get("type") == "Feature":
            raw_features = [data]
        else:
            raw_features = [{"type": "Feature", "geometry": data, "properties": {}}]

    features: list[LayerFeature] = []
    minx, miny, maxx, maxy = float("inf"), float("inf"), float("-inf"), float("-inf")

    for idx, f in enumerate(raw_features):
        raw_geom = f.get("geometry")
        if not raw_geom:
            continue
        v_res = validate_and_repair_geometry(raw_geom, allow_repair=allow_repair)
        if not v_res.is_valid or v_res.geometry is None:
            continue

        geom = transform_geometry(v_res.geometry, from_epsg=source_crs, to_epsg=PROJECT_CRS_EPSG)
        b = geom.bounds
        minx = min(minx, b[0])
        miny = min(miny, b[1])
        maxx = max(maxx, b[2])
        maxy = max(maxy, b[3])

        features.append(
            LayerFeature(
                id=f.get("id", idx),
                geometry=geom,
                geojson=v_res.geojson or {},
                properties=f.get("properties", {}),
                repaired=v_res.repaired,
                repair_method=v_res.method,
            )
        )

    bounds = (minx, miny, maxx, maxy) if features else None
    metadata = LayerMetadata(
        layer_id=layer_id,
        name=name or layer_id,
        layer_type="vector",
        source_crs_epsg=source_crs,
        target_crs_epsg=PROJECT_CRS_EPSG,
        feature_count=len(features),
        bounds=bounds,
        description=description,
        is_demo_fixture=is_demo_fixture,
        provenance=provenance,
    )
    return LoadedLayer(metadata=metadata, features=features)
