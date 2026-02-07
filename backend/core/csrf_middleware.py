"""CSRF middleware for FastAPI applications.

Implements the double-submit cookie pattern for CSRF protection.
Validates that state-changing requests include a CSRF token that
matches the value stored in a cookie.
"""

from collections.abc import Awaitable, Callable, Sequence

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from core.cookie_config import get_cookie_config
from core.cors import is_origin_allowed
from core.csrf import validate_csrf_token

# HTTP methods that modify state and require CSRF protection
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_websocket_upgrade(scope: dict) -> bool:
    """Check if request is a WebSocket upgrade (BaseHTTPMiddleware breaks for these)."""
    if scope.get("type") == "websocket":
        return True
    if scope.get("type") != "http":
        return False
    headers = dict(scope.get("headers", []))
    upgrade = headers.get(b"upgrade", b"").decode("latin-1").lower()
    return upgrade == "websocket"


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware that validates CSRF tokens for unsafe HTTP methods.

    Implements double-submit cookie pattern:
    1. Server sets a CSRF token in a readable cookie
    2. Client reads cookie and includes token in X-CSRF-Token header
    3. Middleware compares cookie value with header value
    4. Request proceeds only if tokens match

    Attributes:
        exempt_paths: Set of paths that skip CSRF validation.
            Supports wildcards (e.g., "/api/v1/webhooks/*").
        config: Cookie configuration for token name lookup.
    """

    def __init__(self, app, exempt_paths: Sequence[str] | None = None):
        """Initialize CSRF middleware.

        Args:
            app: The ASGI application to wrap.
            exempt_paths: Optional list of paths to exempt from CSRF validation.
                Supports trailing wildcards (e.g., "/webhooks/*" matches
                "/webhooks/stripe", "/webhooks/stripe/events", etc.).
        """
        super().__init__(app)
        self.exempt_paths = set(exempt_paths or [])
        self.config = get_cookie_config()

    async def __call__(self, scope: dict, receive: object, send: object) -> None:
        """Bypass BaseHTTPMiddleware for WebSocket - it breaks on upgrade (no response returned)."""
        if _is_websocket_upgrade(scope):
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and validate CSRF token if needed.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to invoke the next middleware/handler.

        Returns:
            Response from the next handler if CSRF validation passes,
            or a 403 JSON response if validation fails.
        """
        # Safe methods don't need CSRF protection
        if request.method not in UNSAFE_METHODS:
            return await call_next(request)

        # Check if path is explicitly exempt
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Validate CSRF token using double-submit cookie pattern
        cookie_token = request.cookies.get(self.config.csrf_token_name)
        header_token = request.headers.get("x-csrf-token")

        if not validate_csrf_token(cookie_token, header_token):
            # Build response with CORS headers for cross-origin error visibility
            # Without CORS headers, browsers block the response and show generic errors
            origin = request.headers.get("origin", "")
            headers: dict[str, str] = {}

            if origin and is_origin_allowed(origin):
                headers["Access-Control-Allow-Origin"] = origin
                headers["Access-Control-Allow-Credentials"] = "true"
                headers["Vary"] = "Origin"

            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"},
                headers=headers,
            )

        return await call_next(request)

    def _is_exempt(self, path: str) -> bool:
        """Check if a path is exempt from CSRF validation.

        Args:
            path: The request URL path.

        Returns:
            True if the path matches an exempt pattern, False otherwise.
        """
        # Exact match
        if path in self.exempt_paths:
            return True

        # Wildcard match (e.g., "/webhooks/*" matches "/webhooks/stripe")
        return any(
            exempt.endswith("*") and path.startswith(exempt[:-1])
            for exempt in self.exempt_paths
        )
