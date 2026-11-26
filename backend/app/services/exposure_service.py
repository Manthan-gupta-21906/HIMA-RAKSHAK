"""Spatial exposure service connecting managed GIS layers and hazard outputs."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.geospatial.layer_loader import LoadedLayer
from app.models.location import LocationRecord
from app.repositories.gis_layer_repository import GisLayerRepository
from app.risk.exposure import build_exposure_profile
from app.schemas.common import HazardType, RiskClass
from app.schemas.exposure import (
    ExposureAsset,
    ExposureCountType,
    LocationExposureProfile,
)
from app.schemas.layer import LayerCategory
from app.schemas.risk import RiskAssessmentContract
from app.services.geospatial_service import GeospatialService

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EXPOSURE_LAYERS_DIR = REPO_ROOT / "data" / "layers" / "exposure"

HAZARD_SEVERITY_FACTOR: dict[RiskClass, float] = {
    RiskClass.UNSUPPORTED: 0.0,
    RiskClass.LOW: 0.35,
    RiskClass.MODERATE: 0.65,
    RiskClass.HIGH: 0.90,
    RiskClass.SEVERE: 1.0,
}


class SpatialExposureService:
    """Computes location exposure profiles from managed GIS asset layers and hazard outputs."""

    LAYER_ID = "jk-managed-exposure-assets"

    def __init__(
        self,
        geo_service: GeospatialService | None = None,
        layer_repo: GisLayerRepository | None = None,
        layers_dir: Path | None = None,
    ) -> None:
        self._geo = geo_service or GeospatialService()
        self._layer_repo = layer_repo
        self._layers_dir = layers_dir or DEFAULT_EXPOSURE_LAYERS_DIR
        self._loaded_layer_ids: list[str] = []
        self._load_managed_layers()

    def _load_managed_layers(self) -> None:
        """Load active exposure layers from DB repository first, then GeoJSON files on disk."""
        if self._layer_repo is not None:
            db_layers = self._layer_repo.list_layer_details(
                category=LayerCategory.EXPOSURE.value,
                active_only=True,
            )
            for layer in db_layers:
                if self._geo.get_layer(layer.layer_id) is None:
                    self._geo.load_and_register_geojson(
                        layer.geojson,
                        layer_id=layer.layer_id,
                        name=layer.name,
                        description=layer.description,
                        provenance=layer.provenance,
                    )
                if layer.layer_id not in self._loaded_layer_ids:
                    self._loaded_layer_ids.append(layer.layer_id)
            if self._loaded_layer_ids:
                return

        if self._layers_dir.exists() and self._layers_dir.is_dir():
            for geojson_path in sorted(self._layers_dir.glob("*.geojson")):
                layer_id = geojson_path.stem
                if self._geo.get_layer(layer_id) is None:
                    self._geo.load_and_register_geojson(
                        geojson_path,
                        layer_id=layer_id,
                        name=layer_id.replace("_", " ").title(),
                        description=f"Managed GIS exposure layer ({geojson_path.name})",
                        provenance=f"managed_gis_file:{geojson_path.name}",
                    )
                if layer_id not in self._loaded_layer_ids:
                    self._loaded_layer_ids.append(layer_id)

    def _get_active_layers(self) -> list[LoadedLayer]:
        layers: list[LoadedLayer] = []
        for lid in self._loaded_layer_ids:
            layer = self._geo.get_layer(lid)
            if layer is not None:
                layers.append(layer)
        return layers

    def calculate_exposure(
        self,
        location: LocationRecord,
        hazard_assessment: RiskAssessmentContract | None = None,
        radius_km: float = 10.0,
    ) -> LocationExposureProfile:
        """Intersect managed GIS layer features near ``location`` and scale by hazard output."""
        layers = self._get_active_layers()
        if not layers:
            return build_exposure_profile(location.location_id, [], available_layers=[])

        scale = 1.0
        target_hazard: HazardType | None = None
        if hazard_assessment is not None:
            target_hazard = hazard_assessment.hazard_type
            scale = HAZARD_SEVERITY_FACTOR.get(hazard_assessment.risk_class, 0.5)

        assets: list[ExposureAsset] = []
        available_layers: set[str] = set()

        for layer in layers:
            layer_id = layer.metadata.layer_id
            for feat in layer.features:
                geom = feat.geometry
                props = feat.properties or {}
                if geom is None:
                    continue
                centroid = geom.centroid
                # Approximate degree-to-km check (~111 km/deg)
                dy = centroid.y - location.latitude
                dx = centroid.x - location.longitude
                dist_km = ((dy**2 + dx**2) ** 0.5) * 111.0
                if dist_km > radius_km:
                    continue

                feat_hazards = props.get("hazards") or []
                if (
                    target_hazard is not None
                    and feat_hazards
                    and target_hazard.value not in feat_hazards
                ):
                    continue

                asset_type = str(props.get("asset_type", "settlement"))
                layer_key = {
                    "settlement": "settlements",
                    "home": "homes",
                    "road": "roads",
                    "critical_facility": "critical_facilities",
                }.get(asset_type, asset_type)
                available_layers.add(layer_key)

                raw_pop = int(props.get("population_affected", 0))
                scaled_pop = int(round(raw_pop * scale)) if scale > 0 else 0
                raw_count_type = str(props.get("count_type", "estimated")).lower()
                count_type = (
                    ExposureCountType.VERIFIED
                    if raw_count_type == ExposureCountType.VERIFIED.value
                    else ExposureCountType.ESTIMATED
                )
                metadata: dict[str, Any] = {
                    "layer_id": layer_id,
                    "provenance": layer.metadata.provenance,
                    "distance_km": round(dist_km, 2),
                }
                if "length_km" in props:
                    metadata["length_km"] = round(float(props["length_km"]) * max(scale, 0.25), 2)

                assets.append(
                    ExposureAsset(
                        asset_id=str(props.get("asset_id", "asset-unknown")),
                        asset_type=asset_type,
                        name=str(props.get("name", "Exposed Asset")),
                        count=int(props.get("count", 1)),
                        count_type=count_type,
                        population_affected=scaled_pop,
                        is_critical=bool(props.get("is_critical", False)),
                        metadata=metadata,
                    )
                )

        return build_exposure_profile(
            location_id=location.location_id,
            assets=assets,
            available_layers=sorted(available_layers),
            evaluated_at=datetime.now(UTC),
        )
