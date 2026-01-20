"""Response caching middleware for FastAPI."""

import hashlib
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add caching headers to responses.

    Improves performance by allowing browsers and CDNs to cache responses.
    """

    def __init__(self, app, cache_control_rules: dict = None):
        super().__init__(app)
        self.cache_control_rules = cache_control_rules or {
            # Public endpoints - cache for 5 minutes
            "/api/subjects": "public, max-age=300, s-maxage=600",
            "/api/tutors": "public, max-age=60, s-maxage=120",
            # Health check - cache for 10 seconds
            "/health": "public, max-age=10",
            # Static content would go here
        }
        self.no_cache_methods = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add cache headers to responses."""
        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add processing time header
        response.headers["X-Process-Time"] = str(process_time)

        # Don't cache mutations
        if request.method in self.no_cache_methods:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

        # Apply cache rules based on path
        for path_prefix, cache_control in self.cache_control_rules.items():
            if request.url.path.startswith(path_prefix):
                response.headers["Cache-Control"] = cache_control
                # Add ETag for conditional requests
                if response.status_code == 200 and hasattr(response, "body"):
                    body_bytes = getattr(response, "body", b"")
                    if body_bytes:
                        etag = hashlib.md5(body_bytes).hexdigest()
                        response.headers["ETag"] = f'"{etag}"'

                        # Check if client has cached version
                        if_none_match = request.headers.get("If-None-Match")
                        if if_none_match and if_none_match.strip('"') == etag:
                            return Response(status_code=304, headers=dict(response.headers))
                return response

        # Default: no cache for authenticated endpoints
        if "Authorization" in request.headers or "api" in request.url.path:
            response.headers["Cache-Control"] = "private, no-cache, no-store, must-revalidate"
        else:
            # Public endpoints get short cache
            response.headers["Cache-Control"] = "public, max-age=30"

        return response
