"""Managed GIS layer registry and upload API routes."""

from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import require_admin, require_any_authenticated
from app.db.session import get_db
from app.geospatial.layer_loader import load_geojson_layer
from app.models.gis_layer import ManagedGisLayerModel  # noqa: F401
from app.repositories.gis_layer_repository import GisLayerRepository
from app.schemas.layer import (
    LayerCategory,
    ManagedLayerCreate,
    ManagedLayerDetail,
    ManagedLayerListResponse,
)

router = APIRouter(prefix="/layers", tags=["layers"])


def _get_db() -> Generator[Session, None, None]:
    yield from get_db()


def get_layer_repo(db: Session = Depends(_get_db)) -> GisLayerRepository:
    return GisLayerRepository(db)


@router.get("", response_model=ManagedLayerListResponse, summary="List managed GIS layers")
def list_layers(
    category: LayerCategory | None = Query(default=None, description="Filter by layer category"),
    active_only: bool = Query(default=True, description="Include only active layers"),
    _user: object = Depends(require_any_authenticated),
    repo: GisLayerRepository = Depends(get_layer_repo),
) -> ManagedLayerListResponse:
    """List managed GIS layers persisted in the spatial registry."""
    items = repo.list_layers(
        category=category.value if category else None,
        active_only=active_only,
    )
    return ManagedLayerListResponse(total=len(items), items=items)


@router.get("/{layer_id}", response_model=ManagedLayerDetail, summary="Get a managed GIS layer")
def get_layer(
    layer_id: str,
    _user: object = Depends(require_any_authenticated),
    repo: GisLayerRepository = Depends(get_layer_repo),
) -> ManagedLayerDetail:
    """Retrieve metadata and normalized EPSG:4326 GeoJSON for a managed GIS layer."""
    layer = repo.get_by_id(layer_id)
    if layer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Managed GIS layer '{layer_id}' not found.",
        )
    return layer


@router.post(
    "",
    response_model=ManagedLayerDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Register or update a managed GIS layer",
)
def upsert_layer(
    payload: ManagedLayerCreate,
    _admin: object = Depends(require_admin),
    repo: GisLayerRepository = Depends(get_layer_repo),
) -> ManagedLayerDetail:
    """Validate, normalize to EPSG:4326, and persist a managed GeoJSON layer (admin only)."""
    try:
        loaded = load_geojson_layer(
            source=payload.geojson,
            layer_id=payload.layer_id,
            name=payload.name,
            description=payload.description,
            provenance=payload.provenance,
            is_demo_fixture=payload.is_demo_fixture,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid GeoJSON layer: {exc}",
        ) from exc

    normalized_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": feat.id,
                "geometry": feat.geojson,
                "properties": feat.properties,
            }
            for feat in loaded.features
        ],
    }

    return repo.upsert_layer(
        layer_id=payload.layer_id,
        name=payload.name,
        layer_category=payload.layer_category.value,
        description=payload.description,
        provenance=payload.provenance,
        is_demo_fixture=payload.is_demo_fixture,
        source_crs_epsg=loaded.metadata.source_crs_epsg,
        feature_count=loaded.metadata.feature_count,
        geojson=normalized_geojson,
    )


@router.delete(
    "/{layer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a managed GIS layer",
)
def deactivate_layer(
    layer_id: str,
    _admin: object = Depends(require_admin),
    repo: GisLayerRepository = Depends(get_layer_repo),
) -> None:
    """Soft-deactivate a managed GIS layer (admin only)."""
    if not repo.deactivate_layer(layer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Managed GIS layer '{layer_id}' not found.",
        )
