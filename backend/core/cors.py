"""
CORS Configuration - Single Source of Truth

All CORS settings are defined here. No other file should parse CORS_ORIGINS
or define CORS-related constants.

Architecture:
- CORSConfig: Immutable configuration dataclass
- get_cors_config(): Reads from environment, returns frozen config
- CORSSafetyNetMiddleware: Ensures CORS headers on ALL responses
- setup_cors(): One-call setup for FastAPI apps

Why multiple layers?
Starlette's CORSMiddleware doesn't add headers to 500 errors or exception
handler responses. We need CORSSafetyNetMiddleware as a backup.
"""

import logging
import os
from dataclasses import dataclass
from typing import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass(frozen=True)
class CORSConfig:
    """Immutable CORS configuration."""

    origins: tuple[str, ...]
    methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    headers: tuple[str, ...] = (
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control",
        "Pragma",
        "X-CSRF-Token",
    )
    expose_headers: tuple[str, ...] = (
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "Content-Disposition",
    )
    max_age: int = 86400
    credentials: bool = True


def get_cors_config() -> CORSConfig:
    """
    Get CORS configuration from environment.

    Priority:
    1. CORS_ORIGINS environment variable (comma-separated)
    2. Environment-based defaults (production vs development)

    Returns:
        Frozen CORSConfig instance
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    raw_origins = os.getenv("CORS_ORIGINS", "")

    if raw_origins:
        origins = tuple(
            o.strip().rstrip("/").lower()
            for o in raw_origins.split(",")
            if o.strip().startswith(("http://", "https://"))
        )
    elif env == "production":
        origins = (
            "https://edustream.valsa.solutions",
            "https://api.valsa.solutions",
        )
    else:
        origins = (
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8000",
        )

    max_age = 86400 if env == "production" else 600

    return CORSConfig(origins=origins, max_age=max_age)


# Global config instance (loaded once)
_config: CORSConfig | None = None


def _get_config() -> CORSConfig:
    """Get or create the global CORS config."""
    global _config
    if _config is None:
        _config = get_cors_config()
    return _config


def is_origin_allowed(origin: str | None) -> bool:
    """Check if an origin is in the allowed list."""
    if not origin:
        return False
    config = _get_config()
    normalized = origin.lower().rstrip("/")
    return normalized in config.origins


# =============================================================================
# MIDDLEWARE
# =============================================================================


class CORSSafetyNetMiddleware(BaseHTTPMiddleware):
    """
    Safety net ensuring CORS headers on ALL responses.

    Why needed: Starlette's CORSMiddleware doesn't add headers to:
    - 500 errors from ServerErrorMiddleware
    - Responses from exception handlers
    - Any response that bypasses the middleware chain

    This middleware runs AFTER CORSMiddleware and adds missing headers.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.config = _get_config()
        self.origins_set = set(self.config.origins)

    async def dispatch(self, request: Request, call_next: Callable):
        origin = request.headers.get("origin", "")
        normalized_origin = origin.lower().rstrip("/") if origin else ""

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"Unhandled exception: {e}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        # Add CORS headers if missing and origin is allowed
        if "access-control-allow-origin" not in response.headers:
            if normalized_origin in self.origins_set:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Vary"] = "Origin"

        return response


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================


def create_cors_exception_handler():
    """
    Create exception handler that includes CORS headers.

    Works for HTTPException, RateLimitExceeded, and any other exception.
    """
    config = _get_config()
    origins_set = set(config.origins)

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        origin = request.headers.get("origin", "")
        normalized_origin = origin.lower().rstrip("/") if origin else ""

        # Determine status code and detail
        if isinstance(exc, HTTPException):
            status_code = exc.status_code
            detail = exc.detail
        elif hasattr(exc, "status_code"):
            status_code = getattr(exc, "status_code", 500)
            detail = str(exc) if str(exc) else "Request failed"
        else:
            status_code = 500
            detail = "Internal server error"

        headers: dict[str, str] = {}
        if normalized_origin in origins_set:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Vary"] = "Origin"

        # Add Retry-After for rate limits
        if hasattr(exc, "retry_after"):
            headers["Retry-After"] = str(getattr(exc, "retry_after", 60))

        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers=headers,
        )

    return handler


# =============================================================================
# SETUP FUNCTION
# =============================================================================


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS for the application.

    Call this once during app initialization. This is the ONLY place
    where CORS middleware and handlers should be configured.

    Args:
        app: FastAPI application instance
    """
    config = _get_config()

    logger.info(f"CORS origins: {list(config.origins)}")
    logger.info(f"CORS max_age: {config.max_age}s")

    # Register exception handlers
    # These run BEFORE middleware for their specific exception types
    try:
        from slowapi.errors import RateLimitExceeded

        handler = create_cors_exception_handler()
        app.add_exception_handler(RateLimitExceeded, handler)
    except ImportError:
        logger.debug("slowapi not installed, skipping rate limit handler")

    app.add_exception_handler(HTTPException, create_cors_exception_handler())

    # Add Starlette's CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.origins),
        allow_credentials=config.credentials,
        allow_methods=list(config.methods),
        allow_headers=list(config.headers),
        expose_headers=list(config.expose_headers),
        max_age=config.max_age,
    )

    # Add safety net middleware (runs AFTER CORSMiddleware in response flow)
    app.add_middleware(CORSSafetyNetMiddleware)
