"""FastAPI application entrypoint for HIMA-RAKSHAK."""

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.locations import router as locations_router
from app.api.routes.observations import router as observations_router
from app.api.routes.risk import router as risk_router
from app.api.routes.sources import router as sources_router
from app.config import Settings, get_settings
from app.core.errors import ErrorDetail, build_error_envelope


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-hazard risk intelligence and early-warning decision-support API.",
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        envelope = build_error_envelope(
            error_code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        )
        data = envelope.model_dump(mode="json")
        data["detail"] = exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=data,
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=" -> ".join(str(loc) for loc in err.get("loc", [])),
                code=err.get("type", "validation_error"),
                message=err.get("msg", "Invalid parameter"),
            )
            for err in exc.errors()
        ]
        envelope = build_error_envelope(
            error_code="VALIDATION_ERROR",
            message="Request parameter validation failed.",
            details=details,
        )
        data = envelope.model_dump(mode="json")
        data["detail"] = exc.errors()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=data,
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

    app.include_router(auth_router)
    app.include_router(locations_router)
    app.include_router(sources_router)
    app.include_router(observations_router)
    app.include_router(risk_router)
    return app


app = create_app()
