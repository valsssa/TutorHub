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
from core.csrf import validate_csrf_token

# HTTP methods that modify state and require CSRF protection
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


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
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed"},
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
