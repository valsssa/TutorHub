"""
OpenTelemetry Distributed Tracing Module

Provides comprehensive distributed tracing capabilities including:
- Trace ID generation and propagation
- FastAPI automatic instrumentation
- SQLAlchemy database query tracing
- External API call tracing (Stripe, Brevo, Zoom)
- Background job tracing
- Log correlation with trace IDs

Configuration:
    TRACING_ENABLED: Enable/disable tracing (default: True in production)
    TRACING_EXPORTER: "jaeger", "otlp", or "console" (default: "console")
    JAEGER_AGENT_HOST: Jaeger agent host (default: "localhost")
    JAEGER_AGENT_PORT: Jaeger agent port (default: 6831)
    OTLP_ENDPOINT: OTLP collector endpoint (default: "http://localhost:4317")
    TRACING_SERVICE_NAME: Service name for traces (default: "edustream-api")
    TRACING_SAMPLE_RATE: Sampling rate 0.0-1.0 (default: 1.0 in dev, 0.1 in prod)
"""

import logging
import os
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

# Context variable for trace ID propagation
_trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_span_id_var: ContextVar[str | None] = ContextVar("span_id", default=None)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# Global state
_tracer_provider = None
_tracer = None
_tracing_enabled = False


# ============================================================================
# Configuration
# ============================================================================


class TracingConfig:
    """Tracing configuration from environment variables."""

    ENABLED: bool = os.getenv("TRACING_ENABLED", "false").lower() == "true"
    EXPORTER: str = os.getenv("TRACING_EXPORTER", "console")  # jaeger, otlp, console
    SERVICE_NAME: str = os.getenv("TRACING_SERVICE_NAME", "edustream-api")

    # Jaeger configuration
    JAEGER_AGENT_HOST: str = os.getenv("JAEGER_AGENT_HOST", "localhost")
    JAEGER_AGENT_PORT: int = int(os.getenv("JAEGER_AGENT_PORT", "6831"))

    # OTLP configuration
    OTLP_ENDPOINT: str = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")

    # Sampling
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    SAMPLE_RATE: float = float(
        os.getenv(
            "TRACING_SAMPLE_RATE",
            "1.0" if os.getenv("ENVIRONMENT", "development").lower() == "development" else "0.1"
        )
    )


# ============================================================================
# Trace ID Management
# ============================================================================


def generate_trace_id() -> str:
    """Generate a new trace ID (32 hex characters)."""
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """Generate a new span ID (16 hex characters)."""
    return uuid.uuid4().hex[:16]


def get_trace_id() -> str | None:
    """Get the current trace ID from context."""
    return _trace_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID in context."""
    _trace_id_var.set(trace_id)


def get_span_id() -> str | None:
    """Get the current span ID from context."""
    return _span_id_var.get()


def set_span_id(span_id: str) -> None:
    """Set the span ID in context."""
    _span_id_var.set(span_id)


def clear_trace_context() -> None:
    """Clear the trace context."""
    _trace_id_var.set(None)
    _span_id_var.set(None)


def get_trace_context() -> dict[str, str | None]:
    """Get the current trace context as a dictionary."""
    return {
        "trace_id": get_trace_id(),
        "span_id": get_span_id(),
    }


# ============================================================================
# OpenTelemetry Initialization
# ============================================================================


def init_tracing() -> bool:
    """
    Initialize OpenTelemetry tracing.

    Returns:
        True if tracing was successfully initialized, False otherwise.
    """
    global _tracer_provider, _tracer, _tracing_enabled

    if not TracingConfig.ENABLED:
        logger.info("Tracing is disabled (TRACING_ENABLED=false)")
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

        # Create resource with service information
        resource = Resource.create({
            "service.name": TracingConfig.SERVICE_NAME,
            "service.version": os.getenv("APP_VERSION", "1.0.0"),
            "deployment.environment": TracingConfig.ENVIRONMENT,
        })

        # Create sampler
        sampler = TraceIdRatioBased(TracingConfig.SAMPLE_RATE)

        # Create tracer provider
        _tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        # Configure exporter based on configuration
        if TracingConfig.EXPORTER == "jaeger":
            _setup_jaeger_exporter(_tracer_provider)
        elif TracingConfig.EXPORTER == "otlp":
            _setup_otlp_exporter(_tracer_provider)
        else:
            _setup_console_exporter(_tracer_provider)

        # Set as global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # Get tracer instance
        _tracer = trace.get_tracer(TracingConfig.SERVICE_NAME)

        _tracing_enabled = True
        logger.info(
            f"Tracing initialized: exporter={TracingConfig.EXPORTER}, "
            f"sample_rate={TracingConfig.SAMPLE_RATE}"
        )
        return True

    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not installed: {e}")
        logger.info("Install with: pip install opentelemetry-api opentelemetry-sdk")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}", exc_info=True)
        return False


def _setup_jaeger_exporter(tracer_provider) -> None:
    """Configure Jaeger exporter."""
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        jaeger_exporter = JaegerExporter(
            agent_host_name=TracingConfig.JAEGER_AGENT_HOST,
            agent_port=TracingConfig.JAEGER_AGENT_PORT,
        )
        tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        logger.info(
            f"Jaeger exporter configured: "
            f"{TracingConfig.JAEGER_AGENT_HOST}:{TracingConfig.JAEGER_AGENT_PORT}"
        )
    except ImportError:
        logger.warning("Jaeger exporter not available, falling back to console")
        _setup_console_exporter(tracer_provider)


def _setup_otlp_exporter(tracer_provider) -> None:
    """Configure OTLP exporter."""
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        otlp_exporter = OTLPSpanExporter(endpoint=TracingConfig.OTLP_ENDPOINT)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"OTLP exporter configured: {TracingConfig.OTLP_ENDPOINT}")
    except ImportError:
        logger.warning("OTLP exporter not available, falling back to console")
        _setup_console_exporter(tracer_provider)


def _setup_console_exporter(tracer_provider) -> None:
    """Configure console exporter for development."""
    try:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(SimpleSpanProcessor(console_exporter))
        logger.info("Console span exporter configured (development mode)")
    except ImportError:
        logger.warning("Console exporter not available")


def shutdown_tracing() -> None:
    """Shutdown tracing and flush any pending spans."""
    global _tracer_provider, _tracing_enabled

    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
            logger.info("Tracing shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down tracing: {e}")

    _tracing_enabled = False


# ============================================================================
# FastAPI Instrumentation
# ============================================================================


def instrument_fastapi(app) -> None:
    """
    Instrument a FastAPI application with automatic tracing.

    Args:
        app: FastAPI application instance
    """
    if not _tracing_enabled:
        logger.debug("Tracing not enabled, skipping FastAPI instrumentation")
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,docs,redoc,openapi.json",
        )
        logger.info("FastAPI instrumentation enabled")
    except ImportError:
        logger.warning(
            "FastAPI instrumentation not available. "
            "Install: pip install opentelemetry-instrumentation-fastapi"
        )
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}")


def uninstrument_fastapi(app) -> None:
    """Remove FastAPI instrumentation."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.uninstrument_app(app)
    except Exception:
        pass


# ============================================================================
# SQLAlchemy Instrumentation
# ============================================================================


def instrument_sqlalchemy(engine) -> None:
    """
    Instrument SQLAlchemy engine with automatic query tracing.

    Args:
        engine: SQLAlchemy engine instance
    """
    if not _tracing_enabled:
        logger.debug("Tracing not enabled, skipping SQLAlchemy instrumentation")
        return

    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            enable_commenter=True,
        )
        logger.info("SQLAlchemy instrumentation enabled")
    except ImportError:
        logger.warning(
            "SQLAlchemy instrumentation not available. "
            "Install: pip install opentelemetry-instrumentation-sqlalchemy"
        )
    except Exception as e:
        logger.error(f"Failed to instrument SQLAlchemy: {e}")


# ============================================================================
# HTTP Client Instrumentation
# ============================================================================


def instrument_httpx() -> None:
    """Instrument httpx client for external API call tracing."""
    if not _tracing_enabled:
        return

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("httpx instrumentation enabled")
    except ImportError:
        logger.debug("httpx instrumentation not available")
    except Exception as e:
        logger.error(f"Failed to instrument httpx: {e}")


def instrument_requests() -> None:
    """Instrument requests library for external API call tracing."""
    if not _tracing_enabled:
        return

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()
        logger.info("requests instrumentation enabled")
    except ImportError:
        logger.debug("requests instrumentation not available")
    except Exception as e:
        logger.error(f"Failed to instrument requests: {e}")


# ============================================================================
# Span Creation Utilities
# ============================================================================


def create_span(
    name: str,
    kind: str = "internal",
    attributes: dict[str, Any] | None = None,
):
    """
    Create a new span context manager.

    Args:
        name: Span name
        kind: Span kind ("internal", "client", "server", "producer", "consumer")
        attributes: Optional span attributes

    Returns:
        Span context manager or no-op context manager if tracing disabled

    Usage:
        with create_span("process_payment", attributes={"booking_id": 123}) as span:
            # ... do work ...
            span.set_attribute("status", "success")
    """
    if not _tracing_enabled or _tracer is None:
        from contextlib import nullcontext

        return nullcontext()

    try:
        from opentelemetry.trace import SpanKind

        kind_map = {
            "internal": SpanKind.INTERNAL,
            "client": SpanKind.CLIENT,
            "server": SpanKind.SERVER,
            "producer": SpanKind.PRODUCER,
            "consumer": SpanKind.CONSUMER,
        }

        return _tracer.start_as_current_span(
            name,
            kind=kind_map.get(kind, SpanKind.INTERNAL),
            attributes=attributes or {},
        )
    except Exception as e:
        logger.debug(f"Failed to create span: {e}")
        from contextlib import nullcontext

        return nullcontext()


def trace_function(
    name: str | None = None,
    kind: str = "internal",
    attributes: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """
    Decorator to trace a function execution.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        attributes: Optional span attributes

    Usage:
        @trace_function("process_booking")
        def process_booking(booking_id: int):
            ...

        @trace_function(attributes={"service": "stripe"})
        async def charge_card(amount: int):
            ...
    """

    def decorator(func: F) -> F:
        span_name = name or func.__name__

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with create_span(span_name, kind=kind, attributes=attributes):
                return func(*args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with create_span(span_name, kind=kind, attributes=attributes):
                return await func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


# ============================================================================
# External Service Tracing Helpers
# ============================================================================


def trace_stripe_call(operation: str, **attributes):
    """
    Create a span for Stripe API calls.

    Args:
        operation: Stripe operation name (e.g., "checkout.session.create")
        **attributes: Additional span attributes

    Usage:
        with trace_stripe_call("checkout.session.create", booking_id=123):
            stripe.checkout.Session.create(...)
    """
    return create_span(
        f"stripe.{operation}",
        kind="client",
        attributes={
            "rpc.system": "stripe",
            "rpc.service": "Stripe API",
            "rpc.method": operation,
            **attributes,
        },
    )


def trace_brevo_call(operation: str, **attributes):
    """
    Create a span for Brevo (email) API calls.

    Args:
        operation: Brevo operation name (e.g., "send_transac_email")
        **attributes: Additional span attributes

    Usage:
        with trace_brevo_call("send_transac_email", to_email="user@example.com"):
            api.send_transac_email(...)
    """
    return create_span(
        f"brevo.{operation}",
        kind="client",
        attributes={
            "rpc.system": "brevo",
            "rpc.service": "Brevo Email API",
            "rpc.method": operation,
            **attributes,
        },
    )


def trace_zoom_call(operation: str, **attributes):
    """
    Create a span for Zoom API calls.

    Args:
        operation: Zoom operation name (e.g., "create_meeting")
        **attributes: Additional span attributes

    Usage:
        with trace_zoom_call("create_meeting", booking_id=123):
            zoom_client.create_meeting(...)
    """
    return create_span(
        f"zoom.{operation}",
        kind="client",
        attributes={
            "rpc.system": "zoom",
            "rpc.service": "Zoom API",
            "rpc.method": operation,
            **attributes,
        },
    )


def trace_google_calendar_call(operation: str, **attributes):
    """
    Create a span for Google Calendar API calls.

    Args:
        operation: Calendar operation name (e.g., "create_event")
        **attributes: Additional span attributes
    """
    return create_span(
        f"google_calendar.{operation}",
        kind="client",
        attributes={
            "rpc.system": "google",
            "rpc.service": "Google Calendar API",
            "rpc.method": operation,
            **attributes,
        },
    )


# ============================================================================
# Background Job Tracing
# ============================================================================


def trace_background_job(job_name: str, **attributes):
    """
    Create a span for background job execution.

    Args:
        job_name: Name of the background job
        **attributes: Additional span attributes

    Usage:
        with trace_background_job("expire_requests"):
            # ... job logic ...
    """
    # Generate new trace context for background jobs
    trace_id = generate_trace_id()
    set_trace_id(trace_id)

    return create_span(
        f"job.{job_name}",
        kind="consumer",
        attributes={
            "job.name": job_name,
            "job.type": "scheduled",
            **attributes,
        },
    )


# ============================================================================
# Logging Integration
# ============================================================================


class TraceIdFilter(logging.Filter):
    """
    Logging filter that adds trace ID to log records.

    Usage:
        handler = logging.StreamHandler()
        handler.addFilter(TraceIdFilter())

        # Format with trace_id
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [trace_id=%(trace_id)s] - %(message)s'
        )
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace_id and span_id to log record."""
        record.trace_id = get_trace_id() or "none"
        record.span_id = get_span_id() or "none"
        return True


def configure_logging_with_trace_id() -> None:
    """
    Configure the root logger to include trace IDs in all log messages.

    Call this after initializing tracing to enable log correlation.
    """
    # Add filter to root logger
    root_logger = logging.getLogger()

    # Check if filter already added
    for f in root_logger.filters:
        if isinstance(f, TraceIdFilter):
            return

    trace_filter = TraceIdFilter()
    root_logger.addFilter(trace_filter)

    # Update format for existing handlers
    new_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[trace_id=%(trace_id)s] - [%(filename)s:%(lineno)d] - %(message)s"
    )

    for handler in root_logger.handlers:
        handler.setFormatter(logging.Formatter(new_format))

    logger.info("Logging configured with trace ID correlation")


# ============================================================================
# Convenience function for full setup
# ============================================================================


def setup_tracing(app=None, engine=None) -> bool:
    """
    Convenience function to set up all tracing components.

    Args:
        app: FastAPI application instance (optional)
        engine: SQLAlchemy engine instance (optional)

    Returns:
        True if tracing was successfully set up, False otherwise

    Usage:
        from core.tracing import setup_tracing
        from database import engine

        app = FastAPI()
        setup_tracing(app=app, engine=engine)
    """
    if not init_tracing():
        return False

    # Configure logging
    configure_logging_with_trace_id()

    # Instrument FastAPI
    if app is not None:
        instrument_fastapi(app)

    # Instrument SQLAlchemy
    if engine is not None:
        instrument_sqlalchemy(engine)

    # Instrument HTTP clients
    instrument_httpx()
    instrument_requests()

    return True


def is_tracing_enabled() -> bool:
    """Check if tracing is currently enabled."""
    return _tracing_enabled
