"""Tests for the response cache middleware."""

import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request, Response

from core.response_cache import ResponseCacheMiddleware


class TestResponseCacheMiddleware:
    """Tests for ResponseCacheMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return ResponseCacheMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url.path = "/api/test"
        request.headers = {}
        return request

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        response = MagicMock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response

    def test_init_default_rules(self, app):
        """Test middleware initializes with default cache rules."""
        middleware = ResponseCacheMiddleware(app)

        assert "/api/subjects" in middleware.cache_control_rules
        assert "/api/tutors" in middleware.cache_control_rules
        assert "/health" in middleware.cache_control_rules

    def test_init_custom_rules(self, app):
        """Test middleware initializes with custom rules."""
        custom_rules = {"/api/custom": "public, max-age=600"}
        middleware = ResponseCacheMiddleware(app, cache_control_rules=custom_rules)

        assert "/api/custom" in middleware.cache_control_rules
        assert middleware.cache_control_rules["/api/custom"] == "public, max-age=600"

    def test_no_cache_methods(self, middleware):
        """Test non-cacheable methods are defined."""
        assert "POST" in middleware.no_cache_methods
        assert "PUT" in middleware.no_cache_methods
        assert "PATCH" in middleware.no_cache_methods
        assert "DELETE" in middleware.no_cache_methods
        assert "GET" not in middleware.no_cache_methods

    @pytest.mark.asyncio
    async def test_adds_process_time_header(self, middleware, mock_request):
        """Test middleware adds X-Process-Time header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "X-Process-Time" in response.headers

    @pytest.mark.asyncio
    async def test_no_cache_for_post(self, middleware, mock_request):
        """Test POST requests get no-cache headers."""
        mock_request.method = "POST"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "no-store" in response.headers.get("Cache-Control", "")
        assert response.headers.get("Pragma") == "no-cache"
        assert response.headers.get("Expires") == "0"

    @pytest.mark.asyncio
    async def test_no_cache_for_put(self, middleware, mock_request):
        """Test PUT requests get no-cache headers."""
        mock_request.method = "PUT"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "no-store" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_no_cache_for_delete(self, middleware, mock_request):
        """Test DELETE requests get no-cache headers."""
        mock_request.method = "DELETE"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "no-store" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_cache_subjects_endpoint(self, middleware, mock_request):
        """Test /api/subjects endpoint gets cache headers."""
        mock_request.url.path = "/api/subjects"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "public" in response.headers.get("Cache-Control", "")
        assert "max-age=300" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_cache_tutors_endpoint(self, middleware, mock_request):
        """Test /api/tutors endpoint gets cache headers."""
        mock_request.url.path = "/api/tutors"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "public" in response.headers.get("Cache-Control", "")
        assert "max-age=60" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_cache_health_endpoint(self, middleware, mock_request):
        """Test /health endpoint gets cache headers."""
        mock_request.url.path = "/health"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "public" in response.headers.get("Cache-Control", "")
        assert "max-age=10" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_etag_generation(self, middleware, mock_request):
        """Test ETag is generated for cacheable responses."""
        mock_request.url.path = "/api/subjects"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.body = b'{"data": "test"}'
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "ETag" in response.headers
        expected_etag = hashlib.sha256(b'{"data": "test"}').hexdigest()
        assert response.headers["ETag"] == f'"{expected_etag}"'

    @pytest.mark.asyncio
    async def test_304_response_for_matching_etag(self, middleware, mock_request):
        """Test 304 response when If-None-Match matches ETag."""
        body = b'{"data": "test"}'
        etag = hashlib.sha256(body).hexdigest()

        mock_request.url.path = "/api/subjects"
        mock_request.headers = {"If-None-Match": f'"{etag}"'}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.body = body
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 304

    @pytest.mark.asyncio
    async def test_no_etag_for_error_responses(self, middleware, mock_request):
        """Test ETag is not generated for error responses."""
        mock_request.url.path = "/api/subjects"
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {}
        mock_response.body = b'{"error": "test"}'
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "ETag" not in response.headers

    @pytest.mark.asyncio
    async def test_no_cache_for_authenticated_endpoints(self, middleware, mock_request):
        """Test authenticated endpoints get no-cache headers."""
        mock_request.url.path = "/api/user/profile"
        mock_request.headers = {"Authorization": "Bearer token123"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "private" in response.headers.get("Cache-Control", "")
        assert "no-cache" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_default_cache_for_api_without_auth(self, middleware, mock_request):
        """Test API endpoints without auth get private cache."""
        mock_request.url.path = "/api/unknown"
        mock_request.headers = {}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "Cache-Control" in response.headers

    @pytest.mark.asyncio
    async def test_public_cache_for_non_api(self, middleware, mock_request):
        """Test non-API endpoints get short public cache."""
        mock_request.url.path = "/static/file.js"
        mock_request.headers = {}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "public" in response.headers.get("Cache-Control", "")
        assert "max-age=30" in response.headers.get("Cache-Control", "")

    @pytest.mark.asyncio
    async def test_process_time_is_float(self, middleware, mock_request):
        """Test X-Process-Time is a valid float string."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        process_time = response.headers.get("X-Process-Time")
        assert process_time is not None
        assert float(process_time) >= 0


class TestCacheRuleMatching:
    """Tests for cache rule path matching."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware with custom rules."""
        return ResponseCacheMiddleware(
            app,
            cache_control_rules={
                "/api/v1/public": "public, max-age=600",
                "/api/v1/users": "private, max-age=60",
            },
        )

    @pytest.mark.asyncio
    async def test_prefix_matching(self, middleware):
        """Test cache rules match by prefix."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/public/items"
        mock_request.headers = {}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "public, max-age=600" == response.headers.get("Cache-Control")

    @pytest.mark.asyncio
    async def test_first_matching_rule_wins(self, middleware):
        """Test first matching cache rule is applied."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/v1/users/profile"
        mock_request.headers = {}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "private, max-age=60" == response.headers.get("Cache-Control")


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return ResponseCacheMiddleware(app)

    @pytest.mark.asyncio
    async def test_empty_body(self, middleware):
        """Test handling empty response body."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/subjects"
        mock_request.headers = {}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.body = b""
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "ETag" not in response.headers

    @pytest.mark.asyncio
    async def test_no_body_attribute(self, middleware):
        """Test handling response without body attribute."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/subjects"
        mock_request.headers = {}

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.headers = {}
        del mock_response.body
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response is not None

    @pytest.mark.asyncio
    async def test_patch_method_no_cache(self, middleware):
        """Test PATCH method gets no-cache headers."""
        mock_request = MagicMock(spec=Request)
        mock_request.method = "PATCH"
        mock_request.url.path = "/api/users/1"
        mock_request.headers = {}

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert "no-store" in response.headers.get("Cache-Control", "")
