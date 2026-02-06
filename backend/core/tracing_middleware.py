"""
Tracing Middleware for FastAPI

Provides HTTP request/response tracing with:
- Automatic trace ID generation for incoming requests
- Trace ID propagation through request context
- Trace ID in response headers for debugging
- Error capture with trace context
- Request timing metrics
"""

import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.tracing import (
    clear_trace_context,
    generate_span_id,
    generate_trace_id,
    get_trace_id,
    set_span_id,
    set_trace_id,
)

logger = logging.getLogger(__name__)

# Header names for trace context propagation
TRACE_ID_HEADER = "X-Trace-ID"
SPAN_ID_HEADER = "X-Span-ID"
PARENT_SPAN_HEADER = "X-Parent-Span-ID"

# W3C Trace Context headers (for compatibility)
W3C_TRACEPARENT_HEADER = "traceparent"
W3C_TRACESTATE_HEADER = "tracestate"


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add distributed tracing to all HTTP requests.

    Features:
    - Generates or extracts trace ID from incoming request headers
    - Sets trace context for the duration of the request
    - Adds trace ID to response headers
    - Captures request timing and error information
    - Supports W3C Trace Context format

    Usage:
        from core.tracing_middleware import TracingMiddleware

        app.add_middleware(TracingMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: set[str] | None = None,
    ):
        """
        Initialize tracing middleware.

        Args:
            app: ASGI application
            excluded_paths: Paths to exclude from tracing (e.g., health checks)
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or {"/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tracing context."""
        # Skip tracing for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Extract or generate trace ID
        trace_id = self._extract_trace_id(request)
        span_id = generate_span_id()

        # Set trace context
        set_trace_id(trace_id)
        set_span_id(span_id)

        # Store in request state for access in handlers
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # Record request start time
        start_time = time.perf_counter()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Add trace headers to response
            response.headers[TRACE_ID_HEADER] = trace_id
            response.headers[SPAN_ID_HEADER] = span_id

            # Log request completion
            logger.debug(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration_ms:.2f}ms "
                f"trace_id={trace_id}"
            )

            return response

        except Exception as exc:
            # Calculate duration even for errors
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log error with trace context
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={type(exc).__name__}: {exc} "
                f"duration={duration_ms:.2f}ms trace_id={trace_id}",
                exc_info=True,
            )

            # Re-raise to let FastAPI handle the error
            raise

        finally:
            # Clear trace context
            clear_trace_context()

    def _extract_trace_id(self, request: Request) -> str:
        """
        Extract trace ID from request headers or generate a new one.

        Supports:
        - Custom X-Trace-ID header
        - W3C traceparent header

        Args:
            request: FastAPI request object

        Returns:
            Trace ID string
        """
        # Check for custom trace ID header
        trace_id = request.headers.get(TRACE_ID_HEADER)
        if trace_id and self._is_valid_trace_id(trace_id):
            return trace_id

        # Check for W3C traceparent header
        traceparent = request.headers.get(W3C_TRACEPARENT_HEADER)
        if traceparent:
            extracted_id = self._parse_traceparent(traceparent)
            if extracted_id:
                return extracted_id

        # Generate new trace ID
        return generate_trace_id()

    def _is_valid_trace_id(self, trace_id: str) -> bool:
        """Validate trace ID format (32 hex characters)."""
        if not trace_id or len(trace_id) != 32:
            return False
        try:
            int(trace_id, 16)
            return True
        except ValueError:
            return False

    def _parse_traceparent(self, traceparent: str) -> str | None:
        """
        Parse W3C traceparent header.

        Format: {version}-{trace-id}-{parent-id}-{trace-flags}
        Example: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01

        Args:
            traceparent: W3C traceparent header value

        Returns:
            Extracted trace ID or None if invalid
        """
        try:
            parts = traceparent.split("-")
            if len(parts) >= 2:
                trace_id = parts[1]
                if self._is_valid_trace_id(trace_id):
                    return trace_id
        except Exception:
            pass
        return None


def get_request_trace_id(request: Request) -> str | None:
    """
    Get trace ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Trace ID or None if not set
    """
    return getattr(request.state, "trace_id", None)


def get_request_span_id(request: Request) -> str | None:
    """
    Get span ID from request state.

    Args:
        request: FastAPI request object

    Returns:
        Span ID or None if not set
    """
    return getattr(request.state, "span_id", None)


def add_trace_context_to_headers(headers: dict[str, str]) -> dict[str, str]:
    """
    Add trace context headers for outgoing requests.

    Use this when making HTTP calls to other services to propagate
    the trace context.

    Args:
        headers: Existing headers dictionary

    Returns:
        Headers with trace context added

    Usage:
        headers = {"Authorization": "Bearer ..."}
        headers = add_trace_context_to_headers(headers)
        response = httpx.get(url, headers=headers)
    """
    trace_id = get_trace_id()
    if trace_id:
        headers[TRACE_ID_HEADER] = trace_id
        # Also add W3C format for compatibility
        span_id = generate_span_id()
        headers[W3C_TRACEPARENT_HEADER] = f"00-{trace_id}-{span_id}-01"
    return headers
