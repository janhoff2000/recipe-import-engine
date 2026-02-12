"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from recipe_importer import __version__
from recipe_importer.admin import router as admin_router
from recipe_importer.api import router as api_router
from recipe_importer.config import get_settings
from recipe_importer.core.exceptions import (
    ExtractionError,
    FetchError,
    NoRecipeFoundError,
    PlatformAuthError,
    PlatformNotSupportedError,
    PlatformRateLimitError,
)
from recipe_importer.tracking.store import TrackingStore
from recipe_importer.tracking.tracker import Tracker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle: httpx client, tracking DB."""
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Create shared httpx client
    http_client = httpx.AsyncClient(timeout=30.0)

    # Initialize tracking store
    tracking_store = TrackingStore(settings.tracking_db_path)
    await tracking_store.init()
    tracker = Tracker(tracking_store)

    # Store on app state so routes can access them
    app.state.http_client = http_client
    app.state.tracking_store = tracking_store
    app.state.tracker = tracker

    logger.info("Recipe Import Engine v%s started", __version__)

    yield

    # Cleanup
    await http_client.aclose()
    await tracking_store.close()
    logger.info("Shutdown complete")


async def _inject_state(
    request: Request,
    call_next: Callable[[Request], Coroutine[Any, Any, Response]],
) -> Response:
    """Middleware to propagate app state to request state."""
    request.state.http_client = request.app.state.http_client
    request.state.tracking_store = request.app.state.tracking_store
    request.state.tracker = request.app.state.tracker
    return await call_next(request)


async def _handle_platform_not_supported(
    _request: Request, exc: PlatformNotSupportedError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "platform_not_supported", "detail": str(exc)},
    )


async def _handle_no_recipe(_request: Request, exc: NoRecipeFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "no_recipe_found", "detail": str(exc)},
    )


async def _handle_platform_auth(_request: Request, exc: PlatformAuthError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": "platform_auth_error", "detail": str(exc)},
    )


async def _handle_rate_limit(_request: Request, exc: PlatformRateLimitError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "rate_limit_exceeded", "detail": str(exc)},
    )


async def _handle_fetch_error(_request: Request, exc: FetchError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "fetch_error", "detail": str(exc)},
    )


async def _handle_extraction_error(_request: Request, exc: ExtractionError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "extraction_error", "detail": str(exc)},
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Recipe extraction service with model comparison and tracking",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # State injection middleware
    app.middleware("http")(_inject_state)

    # Exception handlers
    app.exception_handler(PlatformNotSupportedError)(_handle_platform_not_supported)
    app.exception_handler(NoRecipeFoundError)(_handle_no_recipe)
    app.exception_handler(PlatformAuthError)(_handle_platform_auth)
    app.exception_handler(PlatformRateLimitError)(_handle_rate_limit)
    app.exception_handler(FetchError)(_handle_fetch_error)
    app.exception_handler(ExtractionError)(_handle_extraction_error)

    # Include routers
    app.include_router(api_router)
    app.include_router(admin_router)

    return app


# Create app instance
app = create_app()


def run() -> None:
    """Run the development server."""
    uvicorn.run(
        "recipe_importer.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
