"""FastAPI application entrypoint for HIMA-RAKSHAK."""

from fastapi import Depends, FastAPI

from app.api.routes.locations import router as locations_router
from app.config import Settings, get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-hazard risk intelligence and early-warning decision-support API.",
    )

    @app.get("/health", tags=["system"])
    def health_check(cfg: Settings = Depends(get_settings)) -> dict[str, str]:
        """Return service health and runtime metadata."""
        return {
            "status": "ok",
            "service": cfg.app_name,
            "version": cfg.app_version,
            "environment": cfg.app_env,
        }

    app.include_router(locations_router)
    return app


app = create_app()
