"""Spatial exposure service connecting stored geospatial layers and hazard outputs."""

from datetime import UTC, datetime
from typing import Any

from app.models.location import LocationRecord
from app.risk.exposure import build_exposure_profile
from app.schemas.common import HazardType, RiskClass
from app.schemas.exposure import (
    ExposureAsset,
    ExposureCountType,
    LocationExposureProfile,
)
from app.schemas.risk import RiskAssessmentContract
from app.services.geospatial_service import GeospatialService

# Pilot geospatial asset layers (GeoJSON FeatureCollection normalized to EPSG:4326)
PILOT_EXPOSURE_GEOJSON: dict[str, Any] = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.7973, 34.0837]},
            "properties": {
                "asset_id": "asset-sgr-settlement-1",
                "asset_type": "settlement",
                "name": "Dal Lake & Jhelum Bund Ward",
                "count": 3,
                "population_affected": 18500,
                "is_critical": False,
                "hazards": ["flood"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.8010, 34.0850]},
            "properties": {
                "asset_id": "asset-sgr-homes-1",
                "asset_type": "home",
                "name": "Jhelum Floodplain Residences",
                "count": 3400,
                "population_affected": 0,
                "is_critical": False,
                "hazards": ["flood"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.7950, 34.0810]},
            "properties": {
                "asset_id": "asset-sgr-road-1",
                "asset_type": "road",
                "name": "Jhelum Bund & Residency Road",
                "count": 1,
                "length_km": 14.5,
                "population_affected": 0,
                "is_critical": False,
                "hazards": ["flood"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.7990, 34.0860]},
            "properties": {
                "asset_id": "asset-sgr-crit-1",
                "asset_type": "critical_facility",
                "name": "SMHS District Hospital & Substations",
                "count": 3,
                "population_affected": 0,
                "is_critical": True,
                "hazards": ["flood"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.3805, 34.0484]},
            "properties": {
                "asset_id": "asset-gul-settlement-1",
                "asset_type": "settlement",
                "name": "Gulmarg Gondola & Affarwat Sector",
                "count": 2,
                "population_affected": 3800,
                "is_critical": False,
                "hazards": ["avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.3820, 34.0490]},
            "properties": {
                "asset_id": "asset-gul-homes-1",
                "asset_type": "home",
                "name": "Gulmarg Ridge Lodges & Quarters",
                "count": 620,
                "population_affected": 0,
                "is_critical": False,
                "hazards": ["avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.3840, 34.0500]},
            "properties": {
                "asset_id": "asset-gul-road-1",
                "asset_type": "road",
                "name": "Tangmarg–Gulmarg Ghat Road",
                "count": 1,
                "length_km": 12.0,
                "population_affected": 0,
                "is_critical": False,
                "hazards": ["avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [74.3790, 34.0470]},
            "properties": {
                "asset_id": "asset-gul-crit-1",
                "asset_type": "critical_facility",
                "name": "Gulmarg PHC & Helipad",
                "count": 2,
                "population_affected": 0,
                "is_critical": True,
                "hazards": ["avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [75.1947, 33.4375]},
            "properties": {
                "asset_id": "asset-ban-settlement-1",
                "asset_type": "settlement",
                "name": "Banihal — NH-44 Corridor",
                "count": 2,
                "population_affected": 9400,
                "is_critical": False,
                "hazards": ["flood", "avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [75.1960, 33.4390]},
            "properties": {
                "asset_id": "asset-ban-road-1",
                "asset_type": "road",
                "name": "NH-44 Ramban–Banihal Stretch",
                "count": 1,
                "length_km": 18.0,
                "population_affected": 0,
                "is_critical": False,
                "hazards": ["flood", "avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [75.1930, 33.4360]},
            "properties": {
                "asset_id": "asset-ban-crit-1",
                "asset_type": "critical_facility",
                "name": "Banihal CHC & Tunnel Control",
                "count": 2,
                "population_affected": 0,
                "is_critical": True,
                "hazards": ["flood", "avalanche"],
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [75.7525, 34.4275]},
            "properties": {
                "asset_id": "asset-drs-road-1",
                "asset_type": "road",
                "name": "Zojila High Pass Approach",
                "count": 1,
                "length_km": 9.5,
                "population_affected": 0,
                "is_critical": False,
                "hazards": ["avalanche"],
            },
        },
    ],
}

HAZARD_SEVERITY_FACTOR: dict[RiskClass, float] = {
    RiskClass.UNSUPPORTED: 0.0,
    RiskClass.LOW: 0.35,
    RiskClass.MODERATE: 0.65,
    RiskClass.HIGH: 0.90,
    RiskClass.SEVERE: 1.0,
}


class SpatialExposureService:
    """Computes location exposure profiles from stored geospatial asset layers and hazard outputs."""

    LAYER_ID = "jk-pilot-exposure-assets"

    def __init__(self, geo_service: GeospatialService | None = None) -> None:
        self._geo = geo_service or GeospatialService()
        if self._geo.get_layer(self.LAYER_ID) is None:
            self._geo.load_and_register_geojson(
                PILOT_EXPOSURE_GEOJSON,
                layer_id=self.LAYER_ID,
                name="J&K Pilot Exposure Assets",
                description="Pilot settlements, homes, roads, and critical facilities",
                provenance="demo_fixture:geospatial_exposure_v1",
            )

    def calculate_exposure(
        self,
        location: LocationRecord,
        hazard_assessment: RiskAssessmentContract | None = None,
        radius_km: float = 10.0,
    ) -> LocationExposureProfile:
        """Intersect stored geospatial layer features near ``location`` and scale by hazard output."""
        layer = self._geo.get_layer(self.LAYER_ID)
        if layer is None:
            return build_exposure_profile(location.location_id, [], available_layers=[])

        scale = 1.0
        target_hazard: HazardType | None = None
        if hazard_assessment is not None:
            target_hazard = hazard_assessment.hazard_type
            scale = HAZARD_SEVERITY_FACTOR.get(hazard_assessment.risk_class, 0.5)

        assets: list[ExposureAsset] = []
        available_layers: set[str] = set()

        for feat in layer.features:
            geom = feat.geometry
            props = feat.properties or {}
            if geom is None:
                continue
            centroid = geom.centroid
            # Approximate degree-to-km check (~111 km/deg)
            dist_km = (((centroid.y - location.latitude) ** 2 + (centroid.x - location.longitude) ** 2) ** 0.5) * 111.0
            if dist_km > radius_km:
                continue

            feat_hazards = props.get("hazards") or []
            if target_hazard is not None and feat_hazards and target_hazard.value not in feat_hazards:
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
            metadata: dict[str, str | float | int | bool] = {
                "layer_id": self.LAYER_ID,
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
                    count_type=ExposureCountType.ESTIMATED,
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
