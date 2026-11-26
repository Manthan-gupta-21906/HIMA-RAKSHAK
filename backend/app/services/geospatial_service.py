"""Service layer for geospatial layer management, geometry repair, and spatial joins."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.geospatial.layer_loader import LoadedLayer, load_geojson_layer
from app.geospatial.spatial_join import (
    DEFAULT_MAX_DISTANCE_KM,
    SpatialJoinMatch,
    batch_spatial_join,
    match_observation_to_location,
)
from app.repositories.location_repository import LocationRepository


class GeospatialService:
    """Orchestrates geospatial operations and layer catalogues."""

    def __init__(self, location_repo: LocationRepository | None = None) -> None:
        self._location_repo = location_repo
        self._layers: dict[str, LoadedLayer] = {}

    def register_layer(self, layer: LoadedLayer) -> None:
        """Cache a loaded layer in the service catalogue."""
        self._layers[layer.metadata.layer_id] = layer

    def get_layer(self, layer_id: str) -> LoadedLayer | None:
        """Retrieve a registered layer by ID."""
        return self._layers.get(layer_id)

    def list_layers(self) -> list[dict[str, Any]]:
        """List summary metadata for all registered layers."""
        return [asdict(layer.metadata) for layer in self._layers.values()]

    def load_and_register_geojson(
        self,
        source: str | Path | dict[str, Any],
        layer_id: str,
        name: str | None = None,
        description: str = "",
        provenance: str = "demo_fixture",
    ) -> LoadedLayer:
        """Load, validate, normalize to EPSG:4326, and cache a GeoJSON layer."""
        loaded = load_geojson_layer(
            source=source,
            layer_id=layer_id,
            name=name,
            description=description,
            provenance=provenance,
        )
        self.register_layer(loaded)
        return loaded

    def match_point(
        self,
        lat: float,
        lon: float,
        *,
        observation_id: str | None = None,
        max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    ) -> SpatialJoinMatch:
        """Match coordinate to nearest pilot location using the repository."""
        locations = self._location_repo.list_all() if self._location_repo else []
        return match_observation_to_location(
            lat=lat,
            lon=lon,
            locations=locations,
            observation_id=observation_id,
            max_distance_km=max_distance_km,
        )

    def match_points_batch(
        self,
        points: list[dict[str, Any]],
        *,
        max_distance_km: float = DEFAULT_MAX_DISTANCE_KM,
    ) -> list[SpatialJoinMatch]:
        """Perform batch spatial joins against pilot locations."""
        locations = self._location_repo.list_all() if self._location_repo else []
        return batch_spatial_join(points, locations, max_distance_km=max_distance_km)
