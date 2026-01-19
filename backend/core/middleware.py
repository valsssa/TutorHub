"""Security middleware for FastAPI application."""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Following OWASP best practices and CLAUDE.md security guidelines.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Relax CSP for OpenAPI docs to avoid breaking Swagger UI assets
        if request.url.path.startswith(("/docs", "/redoc", "/openapi", "/static")):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: https:; "
                "style-src 'self' 'unsafe-inline'; "
                "script-src 'self' https: 'unsafe-inline'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "connect-src 'self'; "
                "img-src 'self' data:; "
                "script-src 'none'; "
                "style-src 'none'; "
                "font-src 'none'; "
                "object-src 'none'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable browser XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy - Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Strict Transport Security - Enforce HTTPS (only in production)
        # Uncomment when deploying to production with HTTPS
        # response.headers["Strict-Transport-Security"] = (
        #     "max-age=31536000; includeSubDomains; preload"
        # )

        # Remove server header to avoid information disclosure
        if "Server" in response.headers:
            del response.headers["Server"]

        return response
