"""FastAPI application entrypoint for HIMA-RAKSHAK."""

import logging

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.auth import router as auth_router
from app.api.routes.locations import router as locations_router
from app.api.routes.observations import router as observations_router
from app.api.routes.risk import router as risk_router
from app.api.routes.sources import router as sources_router
from app.api.routes.warnings import router as warnings_router
from app.config import Settings, get_settings
from app.core.errors import ErrorDetail, build_error_envelope

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-hazard risk intelligence and early-warning decision-support API.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
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

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        envelope = build_error_envelope(
            error_code="INTERNAL_ERROR",
            message="An unexpected internal error occurred.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=envelope.model_dump(mode="json"),
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
    app.include_router(warnings_router)
    return app


app = create_app()
