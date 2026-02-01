"""
CORS Configuration and Middleware

This module provides comprehensive CORS handling that ensures:
1. CORS headers are present on ALL responses (including 4xx/5xx errors)
2. OPTIONS preflight requests are handled correctly
3. Rate limiting doesn't block preflight requests
4. Consistent configuration across environments

CORS Debugging Checklist:
- If browser shows "CORS error", check backend logs for actual error (likely 500)
- If OPTIONS returns 4xx, check rate limiting and authentication
- If specific endpoint fails, verify it's not throwing exceptions before CORS middleware
"""

import logging
import os
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


def get_cors_origins() -> list[str]:
    """
    Get CORS origins from environment or defaults.

    Priority:
    1. CORS_ORIGINS environment variable (comma-separated)
    2. Default list based on ENVIRONMENT

    Returns:
        List of allowed origins (normalized, no trailing slashes)
    """
    raw_origins = os.getenv("CORS_ORIGINS", "")
    env = os.getenv("ENVIRONMENT", "development").lower()

    if raw_origins:
        origins = [
            origin.strip().rstrip("/").lower()
            for origin in raw_origins.split(",")
            if origin.strip() and origin.strip().startswith(("http://", "https://"))
        ]
        if origins:
            return origins

    # Default origins based on environment
    if env == "production":
        return [
            "https://edustream.valsa.solutions",
            "https://api.valsa.solutions",
        ]
    else:
        # Development/staging defaults
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:5173",  # Vite dev server
        ]


def is_cors_origin_allowed(origin: str | None, allowed_origins: list[str]) -> bool:
    """
    Check if an origin is allowed.

    Args:
        origin: The Origin header value from the request
        allowed_origins: List of allowed origins

    Returns:
        True if origin is allowed, False otherwise
    """
    if not origin:
        return False

    normalized_origin = origin.strip().rstrip("/").lower()
    normalized_allowed = [o.lower() for o in allowed_origins]

    return normalized_origin in normalized_allowed


def get_cors_headers(origin: str | None, allowed_origins: list[str]) -> dict[str, str]:
    """
    Generate CORS headers for a response.

    Args:
        origin: The Origin header from the request
        allowed_origins: List of allowed origins

    Returns:
        Dictionary of CORS headers to add to response
    """
    headers = {}

    if origin and is_cors_origin_allowed(origin, allowed_origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, Accept, Origin, "
            "X-Requested-With, X-Request-ID, Cache-Control, Pragma"
        )
        headers["Access-Control-Expose-Headers"] = (
            "X-Request-ID, X-RateLimit-Limit, X-RateLimit-Remaining, "
            "X-RateLimit-Reset, Content-Disposition"
        )
        headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        # Prevent CORS caching issues
        headers["Vary"] = "Origin"

    return headers


class CORSErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures CORS headers are present on ALL responses.

    This middleware addresses the issue where exception handlers (like rate limiting
    or 500 errors) bypass the CORSMiddleware and return responses without CORS headers.

    Browsers interpret missing CORS headers as a CORS violation, even if the actual
    error is a 500 Internal Server Error or 429 Too Many Requests.

    This middleware:
    1. Runs AFTER the standard CORSMiddleware
    2. Catches any response that's missing CORS headers
    3. Adds the appropriate CORS headers based on the request Origin

    Usage:
        Place this middleware BEFORE CORSMiddleware in the stack:

        app.add_middleware(CORSErrorMiddleware)  # Add first (runs after CORS)
        app.add_middleware(CORSMiddleware, ...)  # Add second (runs before)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.allowed_origins = get_cors_origins()
        logger.debug(f"CORSErrorMiddleware initialized with origins: {self.allowed_origins}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")

        # Handle preflight OPTIONS requests that might have been blocked
        if request.method == "OPTIONS":
            # If this reaches here, the standard CORS middleware should have handled it
            # But if it didn't (e.g., due to rate limiting), we handle it here
            response = await call_next(request)

            # Check if CORS headers are missing
            if "access-control-allow-origin" not in [h.lower() for h in response.headers.keys()]:
                cors_headers = get_cors_headers(origin, self.allowed_origins)
                if cors_headers:
                    # Return a proper preflight response
                    return Response(
                        status_code=204,
                        headers=cors_headers,
                    )
            return response

        # Handle regular requests
        try:
            response = await call_next(request)
        except Exception as e:
            # If an exception occurs, create an error response with CORS headers
            logger.error(f"Unhandled exception in request: {e}", exc_info=True)
            cors_headers = get_cors_headers(origin, self.allowed_origins)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers=cors_headers,
            )

        # Check if response is missing CORS headers (common with exception handlers)
        existing_headers = {h.lower() for h in response.headers.keys()}
        if "access-control-allow-origin" not in existing_headers:
            cors_headers = get_cors_headers(origin, self.allowed_origins)
            for key, value in cors_headers.items():
                response.headers[key] = value

        return response


def create_cors_rate_limit_handler(allowed_origins: list[str] | None = None):
    """
    Create a rate limit exception handler that includes CORS headers.

    The default slowapi rate limit handler returns a 429 response without CORS headers,
    which browsers interpret as a CORS error rather than showing the rate limit message.

    Args:
        allowed_origins: List of allowed origins (uses get_cors_origins() if None)

    Returns:
        Exception handler function for RateLimitExceeded errors
    """
    origins = allowed_origins or get_cors_origins()

    async def rate_limit_handler(request: Request, exc) -> JSONResponse:
        origin = request.headers.get("origin")
        cors_headers = get_cors_headers(origin, origins)

        # Get retry-after from the exception if available
        retry_after = getattr(exc, "retry_after", 60)

        response_headers = {
            "Retry-After": str(retry_after),
            **cors_headers,
        }

        return JSONResponse(
            status_code=429,
            content={
                "detail": "Rate limit exceeded",
                "retry_after": retry_after,
            },
            headers=response_headers,
        )

    return rate_limit_handler


def create_cors_http_exception_handler(allowed_origins: list[str] | None = None):
    """
    Create an HTTP exception handler that includes CORS headers.

    This ensures that HTTPException responses (400, 401, 403, 404, etc.)
    include CORS headers so browsers can read the error details.

    Args:
        allowed_origins: List of allowed origins (uses get_cors_origins() if None)

    Returns:
        Exception handler function for HTTPException errors
    """
    from fastapi import HTTPException

    origins = allowed_origins or get_cors_origins()

    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        origin = request.headers.get("origin")
        cors_headers = get_cors_headers(origin, origins)

        content = {"detail": exc.detail}

        # Preserve any additional headers from the exception
        response_headers = dict(exc.headers) if exc.headers else {}
        response_headers.update(cors_headers)

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=response_headers,
        )

    return http_exception_handler


# ============================================================================
# CORS Testing Utilities
# ============================================================================


def create_cors_test_response(request: Request, allowed_origins: list[str] | None = None) -> dict:
    """
    Create a diagnostic response for CORS testing.

    This is useful for debugging CORS issues by showing exactly what
    the server sees and what it would respond with.

    Args:
        request: The incoming request
        allowed_origins: List of allowed origins (uses get_cors_origins() if None)

    Returns:
        Dictionary with CORS diagnostic information
    """
    origins = allowed_origins or get_cors_origins()
    origin = request.headers.get("origin")

    return {
        "cors_debug": {
            "request": {
                "origin": origin,
                "method": request.method,
                "path": str(request.url.path),
                "headers": {
                    "origin": origin,
                    "access-control-request-method": request.headers.get("access-control-request-method"),
                    "access-control-request-headers": request.headers.get("access-control-request-headers"),
                },
            },
            "configuration": {
                "allowed_origins": origins,
                "origin_allowed": is_cors_origin_allowed(origin, origins),
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
            "response_headers": get_cors_headers(origin, origins) if origin else {},
        }
    }
