"""FastAPI application factory and configuration."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings, Settings
from backend.core.exceptions import SatQueryError
from backend.core.logging import get_logger
from .routes import router
from .middleware import SecurityMiddleware

logger = get_logger(__name__)

def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="SatQuery AI",
        version="1.0.0",
        description="Agentic vision-language assistant for multimodal remote-sensing image analysis.",
    )

    # Middleware
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(router, prefix="/api/v1")

    # Exception handlers
    @app.exception_handler(SatQueryError)
    async def satquery_error_handler(request: Request, exc: SatQueryError):
        logger.error(f"SatQueryError: {exc}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": "SatQuery Error", "detail": str(exc), "error_code": "SATQUERY_ERR"}
        )

    # Root redirect
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Startup/shutdown events
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting SatQuery AI API")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down SatQuery AI API")

    return app
