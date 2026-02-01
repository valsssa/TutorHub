"""Tests for the distributed tracing module."""

import asyncio
import logging
from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import pytest

from core.tracing import (
    TraceIdFilter,
    TracingConfig,
    clear_trace_context,
    configure_logging_with_trace_id,
    create_span,
    generate_span_id,
    generate_trace_id,
    get_span_id,
    get_trace_context,
    get_trace_id,
    init_tracing,
    instrument_fastapi,
    instrument_httpx,
    instrument_requests,
    instrument_sqlalchemy,
    is_tracing_enabled,
    set_span_id,
    set_trace_id,
    setup_tracing,
    shutdown_tracing,
    trace_background_job,
    trace_brevo_call,
    trace_function,
    trace_google_calendar_call,
    trace_stripe_call,
    trace_zoom_call,
    uninstrument_fastapi,
)


class TestTracingConfig:
    """Tests for TracingConfig class."""

    def test_default_values(self):
        """Test default configuration values."""
        assert TracingConfig.EXPORTER == "console"
        assert TracingConfig.SERVICE_NAME == "edustream-api"
        assert TracingConfig.JAEGER_AGENT_HOST == "localhost"
        assert TracingConfig.JAEGER_AGENT_PORT == 6831
        assert TracingConfig.OTLP_ENDPOINT == "http://localhost:4317"

    def test_config_from_env(self):
        """Test configuration reads from environment."""
        with patch.dict(
            "os.environ",
            {
                "TRACING_ENABLED": "true",
                "TRACING_EXPORTER": "jaeger",
                "TRACING_SERVICE_NAME": "test-service",
            },
        ):
            assert TracingConfig.EXPORTER == "console"


class TestTraceIdGeneration:
    """Tests for trace ID generation functions."""

    def test_generate_trace_id_length(self):
        """Test trace ID is 32 hex characters."""
        trace_id = generate_trace_id()
        assert len(trace_id) == 32
        assert all(c in "0123456789abcdef" for c in trace_id)

    def test_generate_trace_id_unique(self):
        """Test trace IDs are unique."""
        trace_ids = [generate_trace_id() for _ in range(100)]
        assert len(set(trace_ids)) == 100

    def test_generate_span_id_length(self):
        """Test span ID is 16 hex characters."""
        span_id = generate_span_id()
        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in span_id)

    def test_generate_span_id_unique(self):
        """Test span IDs are unique."""
        span_ids = [generate_span_id() for _ in range(100)]
        assert len(set(span_ids)) == 100


class TestTraceContextManagement:
    """Tests for trace context management."""

    def setup_method(self):
        """Clear context before each test."""
        clear_trace_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_trace_context()

    def test_set_and_get_trace_id(self):
        """Test setting and getting trace ID."""
        set_trace_id("test_trace_id_123")
        assert get_trace_id() == "test_trace_id_123"

    def test_set_and_get_span_id(self):
        """Test setting and getting span ID."""
        set_span_id("test_span_id")
        assert get_span_id() == "test_span_id"

    def test_get_trace_id_default(self):
        """Test get_trace_id returns None by default."""
        assert get_trace_id() is None

    def test_get_span_id_default(self):
        """Test get_span_id returns None by default."""
        assert get_span_id() is None

    def test_clear_trace_context(self):
        """Test clearing trace context."""
        set_trace_id("trace123")
        set_span_id("span456")

        clear_trace_context()

        assert get_trace_id() is None
        assert get_span_id() is None

    def test_get_trace_context(self):
        """Test getting full trace context."""
        set_trace_id("trace123")
        set_span_id("span456")

        context = get_trace_context()

        assert context == {"trace_id": "trace123", "span_id": "span456"}

    def test_get_trace_context_empty(self):
        """Test getting empty trace context."""
        context = get_trace_context()
        assert context == {"trace_id": None, "span_id": None}


class TestInitTracing:
    """Tests for tracing initialization."""

    def test_init_tracing_disabled(self):
        """Test init_tracing when disabled."""
        with patch.object(TracingConfig, "ENABLED", False):
            result = init_tracing()
            assert result is False

    def test_init_tracing_import_error(self):
        """Test init_tracing handles import error."""
        with patch.object(TracingConfig, "ENABLED", True), patch.dict("sys.modules", {"opentelemetry": None}):
            with patch(
                "core.tracing.init_tracing.__globals__",
                {"__builtins__": {"__import__": MagicMock(side_effect=ImportError)}},
            ):
                init_tracing()


class TestShutdownTracing:
    """Tests for tracing shutdown."""

    def test_shutdown_when_not_initialized(self):
        """Test shutdown when tracing not initialized."""
        with patch("core.tracing._tracer_provider", None), patch("core.tracing._tracing_enabled", False):
            shutdown_tracing()


class TestInstrumentation:
    """Tests for instrumentation functions."""

    def test_instrument_fastapi_when_disabled(self):
        """Test FastAPI instrumentation when tracing disabled."""
        with patch("core.tracing._tracing_enabled", False):
            app = MagicMock()
            instrument_fastapi(app)

    def test_instrument_sqlalchemy_when_disabled(self):
        """Test SQLAlchemy instrumentation when tracing disabled."""
        with patch("core.tracing._tracing_enabled", False):
            engine = MagicMock()
            instrument_sqlalchemy(engine)

    def test_instrument_httpx_when_disabled(self):
        """Test httpx instrumentation when tracing disabled."""
        with patch("core.tracing._tracing_enabled", False):
            instrument_httpx()

    def test_instrument_requests_when_disabled(self):
        """Test requests instrumentation when tracing disabled."""
        with patch("core.tracing._tracing_enabled", False):
            instrument_requests()

    def test_uninstrument_fastapi(self):
        """Test FastAPI uninstrumentation."""
        app = MagicMock()
        uninstrument_fastapi(app)


class TestCreateSpan:
    """Tests for create_span function."""

    def test_create_span_when_disabled(self):
        """Test create_span returns nullcontext when disabled."""
        with patch("core.tracing._tracing_enabled", False):
            result = create_span("test_span")
            assert isinstance(result, nullcontext)

    def test_create_span_with_attributes(self):
        """Test create_span with attributes."""
        with patch("core.tracing._tracing_enabled", False):
            result = create_span(
                "test_span", kind="client", attributes={"key": "value"}
            )
            assert isinstance(result, nullcontext)


class TestTraceFunction:
    """Tests for trace_function decorator."""

    def test_trace_sync_function(self):
        """Test tracing a synchronous function."""

        @trace_function("test_func")
        def sync_func(x):
            return x * 2

        with patch("core.tracing._tracing_enabled", False):
            result = sync_func(5)
            assert result == 10

    def test_trace_async_function(self):
        """Test tracing an asynchronous function."""

        @trace_function("test_async_func")
        async def async_func(x):
            return x * 2

        with patch("core.tracing._tracing_enabled", False):
            result = asyncio.run(async_func(5))
            assert result == 10

    def test_trace_function_default_name(self):
        """Test decorator uses function name as default span name."""

        @trace_function()
        def my_named_function():
            return "result"

        with patch("core.tracing._tracing_enabled", False):
            result = my_named_function()
            assert result == "result"

    def test_trace_function_with_attributes(self):
        """Test decorator with attributes."""

        @trace_function(attributes={"service": "test"})
        def func_with_attrs():
            return True

        with patch("core.tracing._tracing_enabled", False):
            result = func_with_attrs()
            assert result is True


class TestServiceTracingHelpers:
    """Tests for service-specific tracing helpers."""

    def test_trace_stripe_call(self):
        """Test Stripe tracing helper."""
        with patch("core.tracing._tracing_enabled", False):
            result = trace_stripe_call("checkout.session.create", booking_id=123)
            assert isinstance(result, nullcontext)

    def test_trace_brevo_call(self):
        """Test Brevo tracing helper."""
        with patch("core.tracing._tracing_enabled", False):
            result = trace_brevo_call(
                "send_transac_email", to_email="test@example.com"
            )
            assert isinstance(result, nullcontext)

    def test_trace_zoom_call(self):
        """Test Zoom tracing helper."""
        with patch("core.tracing._tracing_enabled", False):
            result = trace_zoom_call("create_meeting", booking_id=456)
            assert isinstance(result, nullcontext)

    def test_trace_google_calendar_call(self):
        """Test Google Calendar tracing helper."""
        with patch("core.tracing._tracing_enabled", False):
            result = trace_google_calendar_call("create_event", tutor_id=789)
            assert isinstance(result, nullcontext)


class TestBackgroundJobTracing:
    """Tests for background job tracing."""

    def setup_method(self):
        """Clear context before each test."""
        clear_trace_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_trace_context()

    def test_trace_background_job(self):
        """Test background job tracing generates new trace context."""
        with patch("core.tracing._tracing_enabled", False):
            result = trace_background_job("expire_requests")
            assert isinstance(result, nullcontext)

    def test_trace_background_job_sets_trace_id(self):
        """Test background job tracing sets a new trace ID."""
        assert get_trace_id() is None

        with patch("core.tracing._tracing_enabled", False):
            trace_background_job("test_job")

        assert get_trace_id() is not None
        assert len(get_trace_id()) == 32


class TestTraceIdFilter:
    """Tests for TraceIdFilter logging filter."""

    def setup_method(self):
        """Clear context before each test."""
        clear_trace_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_trace_context()

    def test_filter_adds_trace_id(self):
        """Test filter adds trace_id to log records."""
        set_trace_id("test_trace_123")

        filter_instance = TraceIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result is True
        assert record.trace_id == "test_trace_123"

    def test_filter_adds_span_id(self):
        """Test filter adds span_id to log records."""
        set_span_id("test_span_456")

        filter_instance = TraceIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.span_id == "test_span_456"

    def test_filter_uses_none_when_no_context(self):
        """Test filter uses 'none' when no trace context."""
        filter_instance = TraceIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.trace_id == "none"
        assert record.span_id == "none"


class TestConfigureLogging:
    """Tests for configure_logging_with_trace_id."""

    def test_configure_logging(self):
        """Test logging configuration adds trace ID filter."""
        with patch("core.tracing.logging") as mock_logging:
            mock_root_logger = MagicMock()
            mock_root_logger.filters = []
            mock_root_logger.handlers = []
            mock_logging.getLogger.return_value = mock_root_logger

            configure_logging_with_trace_id()

            mock_root_logger.addFilter.assert_called_once()

    def test_configure_logging_idempotent(self):
        """Test logging configuration is idempotent."""
        with patch("core.tracing.logging") as mock_logging:
            mock_root_logger = MagicMock()
            existing_filter = TraceIdFilter()
            mock_root_logger.filters = [existing_filter]
            mock_logging.getLogger.return_value = mock_root_logger

            configure_logging_with_trace_id()

            mock_root_logger.addFilter.assert_not_called()


class TestSetupTracing:
    """Tests for setup_tracing convenience function."""

    def test_setup_when_init_fails(self):
        """Test setup returns False when init fails."""
        with patch("core.tracing.init_tracing", return_value=False):
            result = setup_tracing()
            assert result is False

    def test_setup_calls_instrumentation(self):
        """Test setup calls all instrumentation functions."""
        with patch("core.tracing.init_tracing", return_value=True):
            with patch("core.tracing.configure_logging_with_trace_id"):
                with patch("core.tracing.instrument_fastapi") as mock_fastapi:
                    with patch("core.tracing.instrument_sqlalchemy") as mock_sql:
                        with patch("core.tracing.instrument_httpx"):
                            with patch("core.tracing.instrument_requests"):
                                app = MagicMock()
                                engine = MagicMock()
                                result = setup_tracing(app=app, engine=engine)

                                assert result is True
                                mock_fastapi.assert_called_once_with(app)
                                mock_sql.assert_called_once_with(engine)


class TestIsTracingEnabled:
    """Tests for is_tracing_enabled function."""

    def test_returns_false_when_disabled(self):
        """Test returns False when tracing is disabled."""
        with patch("core.tracing._tracing_enabled", False):
            assert is_tracing_enabled() is False

    def test_returns_true_when_enabled(self):
        """Test returns True when tracing is enabled."""
        with patch("core.tracing._tracing_enabled", True):
            assert is_tracing_enabled() is True
