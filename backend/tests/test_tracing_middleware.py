"""Tests for the tracing middleware."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response

from core.tracing_middleware import (
    PARENT_SPAN_HEADER,
    SPAN_ID_HEADER,
    TRACE_ID_HEADER,
    W3C_TRACEPARENT_HEADER,
    W3C_TRACESTATE_HEADER,
    TracingMiddleware,
    add_trace_context_to_headers,
    get_request_span_id,
    get_request_trace_id,
)


class TestTracingMiddleware:
    """Tests for TracingMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return TracingMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {}
        request.state = MagicMock()
        return request

    def test_init_default_excluded_paths(self, app):
        """Test default excluded paths."""
        middleware = TracingMiddleware(app)

        assert "/health" in middleware.excluded_paths
        assert "/docs" in middleware.excluded_paths
        assert "/redoc" in middleware.excluded_paths
        assert "/openapi.json" in middleware.excluded_paths

    def test_init_custom_excluded_paths(self, app):
        """Test custom excluded paths."""
        middleware = TracingMiddleware(app, excluded_paths={"/custom", "/path"})

        assert "/custom" in middleware.excluded_paths
        assert "/path" in middleware.excluded_paths
        assert "/health" not in middleware.excluded_paths


class TestDispatch:
    """Tests for the dispatch method."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return TracingMiddleware(MagicMock())

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {}
        request.state = MagicMock()
        return request

    @pytest.mark.asyncio
    async def test_skips_excluded_paths(self, middleware, mock_request):
        """Test excluded paths are not traced."""
        mock_request.url.path = "/health"
        mock_response = MagicMock(spec=Response)
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response == mock_response
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_generates_trace_id(self, middleware, mock_request):
        """Test trace ID is generated."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.set_trace_id") as mock_set_trace:
            with patch("core.tracing_middleware.set_span_id"):
                with patch("core.tracing_middleware.clear_trace_context"):
                    await middleware.dispatch(mock_request, call_next)

                    mock_set_trace.assert_called_once()
                    call_args = mock_set_trace.call_args[0][0]
                    assert len(call_args) == 32

    @pytest.mark.asyncio
    async def test_adds_trace_id_to_response(self, middleware, mock_request):
        """Test trace ID is added to response headers."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.clear_trace_context"):
            response = await middleware.dispatch(mock_request, call_next)

        assert TRACE_ID_HEADER in response.headers
        assert len(response.headers[TRACE_ID_HEADER]) == 32

    @pytest.mark.asyncio
    async def test_adds_span_id_to_response(self, middleware, mock_request):
        """Test span ID is added to response headers."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.clear_trace_context"):
            response = await middleware.dispatch(mock_request, call_next)

        assert SPAN_ID_HEADER in response.headers
        assert len(response.headers[SPAN_ID_HEADER]) == 16

    @pytest.mark.asyncio
    async def test_stores_trace_id_in_request_state(self, middleware, mock_request):
        """Test trace ID is stored in request state."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.clear_trace_context"):
            await middleware.dispatch(mock_request, call_next)

        assert mock_request.state.trace_id is not None
        assert len(mock_request.state.trace_id) == 32

    @pytest.mark.asyncio
    async def test_stores_span_id_in_request_state(self, middleware, mock_request):
        """Test span ID is stored in request state."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.clear_trace_context"):
            await middleware.dispatch(mock_request, call_next)

        assert mock_request.state.span_id is not None
        assert len(mock_request.state.span_id) == 16

    @pytest.mark.asyncio
    async def test_clears_trace_context_after_request(self, middleware, mock_request):
        """Test trace context is cleared after request."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.clear_trace_context") as mock_clear:
            await middleware.dispatch(mock_request, call_next)

            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clears_trace_context_on_exception(self, middleware, mock_request):
        """Test trace context is cleared even on exception."""
        call_next = AsyncMock(side_effect=ValueError("Test error"))

        with patch("core.tracing_middleware.clear_trace_context") as mock_clear:
            with pytest.raises(ValueError):
                await middleware.dispatch(mock_request, call_next)

            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_extracts_trace_id_from_header(self, middleware, mock_request):
        """Test trace ID is extracted from incoming header."""
        mock_request.headers = {TRACE_ID_HEADER: "a" * 32}
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        with patch("core.tracing_middleware.clear_trace_context"):
            response = await middleware.dispatch(mock_request, call_next)

        assert response.headers[TRACE_ID_HEADER] == "a" * 32


class TestExtractTraceId:
    """Tests for trace ID extraction."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return TracingMiddleware(MagicMock())

    def test_extracts_from_custom_header(self, middleware):
        """Test extraction from custom X-Trace-ID header."""
        mock_request = MagicMock()
        mock_request.headers = {TRACE_ID_HEADER: "a" * 32}

        result = middleware._extract_trace_id(mock_request)

        assert result == "a" * 32

    def test_extracts_from_w3c_traceparent(self, middleware):
        """Test extraction from W3C traceparent header."""
        mock_request = MagicMock()
        trace_id = "b" * 32
        mock_request.headers = {
            W3C_TRACEPARENT_HEADER: f"00-{trace_id}-{'c' * 16}-01"
        }
        mock_request.headers.get = (
            lambda key, default=None: mock_request.headers.get(key, default)
        )

        result = middleware._extract_trace_id(mock_request)

        assert result == trace_id

    def test_generates_new_when_no_header(self, middleware):
        """Test new trace ID is generated when no header present."""
        mock_request = MagicMock()
        mock_request.headers = {}
        mock_request.headers.get = lambda key, default=None: None

        result = middleware._extract_trace_id(mock_request)

        assert len(result) == 32

    def test_generates_new_for_invalid_header(self, middleware):
        """Test new trace ID is generated for invalid header."""
        mock_request = MagicMock()
        mock_request.headers = {TRACE_ID_HEADER: "invalid"}
        mock_request.headers.get = (
            lambda key, default=None: mock_request.headers.get(key, default)
        )

        result = middleware._extract_trace_id(mock_request)

        assert result != "invalid"
        assert len(result) == 32


class TestValidateTraceId:
    """Tests for trace ID validation."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return TracingMiddleware(MagicMock())

    def test_valid_trace_id(self, middleware):
        """Test valid trace ID (32 hex chars)."""
        assert middleware._is_valid_trace_id("a" * 32) is True
        assert middleware._is_valid_trace_id("0123456789abcdef" * 2) is True

    def test_invalid_length(self, middleware):
        """Test invalid trace ID length."""
        assert middleware._is_valid_trace_id("a" * 31) is False
        assert middleware._is_valid_trace_id("a" * 33) is False

    def test_invalid_characters(self, middleware):
        """Test invalid characters in trace ID."""
        assert middleware._is_valid_trace_id("g" * 32) is False
        assert middleware._is_valid_trace_id("!" * 32) is False

    def test_empty_trace_id(self, middleware):
        """Test empty trace ID."""
        assert middleware._is_valid_trace_id("") is False
        assert middleware._is_valid_trace_id(None) is False


class TestParseTraceparent:
    """Tests for W3C traceparent parsing."""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance."""
        return TracingMiddleware(MagicMock())

    def test_parse_valid_traceparent(self, middleware):
        """Test parsing valid traceparent header."""
        trace_id = "a" * 32
        traceparent = f"00-{trace_id}-{'b' * 16}-01"

        result = middleware._parse_traceparent(traceparent)

        assert result == trace_id

    def test_parse_invalid_format(self, middleware):
        """Test parsing invalid traceparent format."""
        result = middleware._parse_traceparent("invalid")
        assert result is None

    def test_parse_invalid_trace_id(self, middleware):
        """Test parsing traceparent with invalid trace ID."""
        traceparent = f"00-{'g' * 32}-{'b' * 16}-01"

        result = middleware._parse_traceparent(traceparent)

        assert result is None

    def test_parse_empty_traceparent(self, middleware):
        """Test parsing empty traceparent."""
        result = middleware._parse_traceparent("")
        assert result is None


class TestGetRequestTraceId:
    """Tests for get_request_trace_id function."""

    def test_returns_trace_id_from_state(self):
        """Test returning trace ID from request state."""
        mock_request = MagicMock()
        mock_request.state.trace_id = "test_trace_id"

        result = get_request_trace_id(mock_request)

        assert result == "test_trace_id"

    def test_returns_none_when_not_set(self):
        """Test returning None when trace ID not set."""
        mock_request = MagicMock()
        del mock_request.state.trace_id

        result = get_request_trace_id(mock_request)

        assert result is None


class TestGetRequestSpanId:
    """Tests for get_request_span_id function."""

    def test_returns_span_id_from_state(self):
        """Test returning span ID from request state."""
        mock_request = MagicMock()
        mock_request.state.span_id = "test_span_id"

        result = get_request_span_id(mock_request)

        assert result == "test_span_id"

    def test_returns_none_when_not_set(self):
        """Test returning None when span ID not set."""
        mock_request = MagicMock()
        del mock_request.state.span_id

        result = get_request_span_id(mock_request)

        assert result is None


class TestAddTraceContextToHeaders:
    """Tests for add_trace_context_to_headers function."""

    def test_adds_trace_id_header(self):
        """Test adding trace ID header."""
        with patch("core.tracing_middleware.get_trace_id", return_value="a" * 32):
            headers = {}
            result = add_trace_context_to_headers(headers)

            assert TRACE_ID_HEADER in result
            assert result[TRACE_ID_HEADER] == "a" * 32

    def test_adds_w3c_traceparent_header(self):
        """Test adding W3C traceparent header."""
        with patch("core.tracing_middleware.get_trace_id", return_value="a" * 32):
            headers = {}
            result = add_trace_context_to_headers(headers)

            assert W3C_TRACEPARENT_HEADER in result
            traceparent = result[W3C_TRACEPARENT_HEADER]
            assert traceparent.startswith("00-")
            assert "a" * 32 in traceparent

    def test_preserves_existing_headers(self):
        """Test existing headers are preserved."""
        with patch("core.tracing_middleware.get_trace_id", return_value="a" * 32):
            headers = {"Authorization": "Bearer token", "Custom": "value"}
            result = add_trace_context_to_headers(headers)

            assert result["Authorization"] == "Bearer token"
            assert result["Custom"] == "value"

    def test_no_trace_id_available(self):
        """Test handling when no trace ID is available."""
        with patch("core.tracing_middleware.get_trace_id", return_value=None):
            headers = {"Existing": "header"}
            result = add_trace_context_to_headers(headers)

            assert TRACE_ID_HEADER not in result
            assert result["Existing"] == "header"


class TestHeaderConstants:
    """Tests for header name constants."""

    def test_trace_id_header(self):
        """Test trace ID header name."""
        assert TRACE_ID_HEADER == "X-Trace-ID"

    def test_span_id_header(self):
        """Test span ID header name."""
        assert SPAN_ID_HEADER == "X-Span-ID"

    def test_parent_span_header(self):
        """Test parent span header name."""
        assert PARENT_SPAN_HEADER == "X-Parent-Span-ID"

    def test_w3c_traceparent_header(self):
        """Test W3C traceparent header name."""
        assert W3C_TRACEPARENT_HEADER == "traceparent"

    def test_w3c_tracestate_header(self):
        """Test W3C tracestate header name."""
        assert W3C_TRACESTATE_HEADER == "tracestate"
