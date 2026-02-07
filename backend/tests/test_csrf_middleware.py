"""Tests for CSRF middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from starlette.responses import Response

from core.csrf_middleware import CSRFMiddleware, _is_websocket_upgrade


@pytest.fixture
def mock_app():
    """Create a mock ASGI app."""
    return AsyncMock()


@pytest.fixture
def middleware(mock_app):
    """Create CSRF middleware with exempt paths."""
    return CSRFMiddleware(mock_app, exempt_paths=["/api/v1/auth/login"])


def make_request(method: str, path: str, cookies: dict = None, headers: dict = None):
    """Create a mock request with given parameters."""
    request = MagicMock(spec=Request)
    request.method = method
    # Mock URL object with path attribute
    url_mock = MagicMock()
    url_mock.path = path
    request.url = url_mock
    request.cookies = cookies or {}
    request.headers = headers or {}
    return request


class TestCSRFMiddlewareSafeMethods:
    """Tests for safe HTTP methods that bypass CSRF."""

    @pytest.mark.asyncio
    async def test_get_request_bypasses_csrf(self, middleware):
        """GET requests should not require CSRF validation."""
        request = make_request("GET", "/api/v1/users/me")
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called

    @pytest.mark.asyncio
    async def test_head_request_bypasses_csrf(self, middleware):
        """HEAD requests should not require CSRF validation."""
        request = make_request("HEAD", "/api/v1/users/me")
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called

    @pytest.mark.asyncio
    async def test_options_request_bypasses_csrf(self, middleware):
        """OPTIONS requests should not require CSRF validation."""
        request = make_request("OPTIONS", "/api/v1/bookings")
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called


class TestCSRFMiddlewareExemptPaths:
    """Tests for exempt path handling."""

    @pytest.mark.asyncio
    async def test_exempt_path_bypasses_csrf(self, middleware):
        """Exempt paths should not require CSRF validation."""
        request = make_request("POST", "/api/v1/auth/login")
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called

    @pytest.mark.asyncio
    async def test_wildcard_exempt_path(self, mock_app):
        """Wildcard exempt paths should match all sub-paths."""
        middleware = CSRFMiddleware(mock_app, exempt_paths=["/api/v1/webhooks/*"])
        request = make_request("POST", "/api/v1/webhooks/stripe/payment")
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called

    @pytest.mark.asyncio
    async def test_non_exempt_path_requires_csrf(self, middleware):
        """Non-exempt paths should require CSRF validation."""
        request = make_request("POST", "/api/v1/bookings", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403


class TestCSRFMiddlewareValidation:
    """Tests for CSRF token validation."""

    @pytest.mark.asyncio
    async def test_post_without_csrf_returns_403(self, middleware):
        """POST without CSRF tokens should return 403."""
        request = make_request("POST", "/api/v1/bookings", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_with_valid_csrf_passes(self, middleware):
        """POST with matching CSRF tokens should succeed."""
        csrf_token = "test_csrf_token_value"
        request = make_request(
            "POST",
            "/api/v1/bookings",
            cookies={"csrf_token": csrf_token},
            headers={"x-csrf-token": csrf_token},
        )
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called

    @pytest.mark.asyncio
    async def test_post_with_mismatched_csrf_returns_403(self, middleware):
        """POST with mismatched CSRF tokens should return 403."""
        request = make_request(
            "POST",
            "/api/v1/bookings",
            cookies={"csrf_token": "token_a"},
            headers={"x-csrf-token": "token_b"},
        )
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_with_missing_cookie_returns_403(self, middleware):
        """POST with missing cookie token should return 403."""
        request = make_request(
            "POST",
            "/api/v1/bookings",
            cookies={},
            headers={"x-csrf-token": "some_token"},
        )
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_post_with_missing_header_returns_403(self, middleware):
        """POST with missing header token should return 403."""
        request = make_request(
            "POST",
            "/api/v1/bookings",
            cookies={"csrf_token": "some_token"},
            headers={},
        )
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403


class TestCSRFMiddlewareUnsafeMethods:
    """Tests for all unsafe HTTP methods."""

    @pytest.mark.asyncio
    async def test_put_requires_csrf(self, middleware):
        """PUT requests should require CSRF validation."""
        request = make_request("PUT", "/api/v1/bookings/1", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_patch_requires_csrf(self, middleware):
        """PATCH requests should require CSRF validation."""
        request = make_request("PATCH", "/api/v1/bookings/1", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_requires_csrf(self, middleware):
        """DELETE requests should require CSRF validation."""
        request = make_request("DELETE", "/api/v1/bookings/1", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_put_with_valid_csrf_passes(self, middleware):
        """PUT with valid CSRF should succeed."""
        csrf_token = "valid_token"
        request = make_request(
            "PUT",
            "/api/v1/bookings/1",
            cookies={"csrf_token": csrf_token},
            headers={"x-csrf-token": csrf_token},
        )
        inner_called = False

        async def call_next(req):
            nonlocal inner_called
            inner_called = True
            return Response()

        await middleware.dispatch(request, call_next)
        assert inner_called


class TestCSRFMiddlewareErrorResponse:
    """Tests for error response format."""

    @pytest.mark.asyncio
    async def test_403_response_has_json_content(self, middleware):
        """403 response should include JSON error detail."""
        request = make_request("POST", "/api/v1/bookings", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403
        # JSONResponse body is bytes
        assert b"CSRF validation failed" in response.body

    @pytest.mark.asyncio
    async def test_403_response_includes_cors_headers_for_allowed_origin(self, middleware):
        """403 response should include CORS headers for allowed origins."""
        allowed_origin = "https://edustream.valsa.solutions"
        request = make_request(
            "POST",
            "/api/v1/bookings",
            cookies={},
            headers={"origin": allowed_origin},
        )

        with patch("core.csrf_middleware.is_origin_allowed", return_value=True):
            response = await middleware.dispatch(
                request, lambda r: AsyncMock(return_value=Response())()
            )

        assert response.status_code == 403
        assert response.headers.get("access-control-allow-origin") == allowed_origin
        assert response.headers.get("access-control-allow-credentials") == "true"
        assert response.headers.get("vary") == "Origin"

    @pytest.mark.asyncio
    async def test_403_response_no_cors_headers_for_disallowed_origin(self, middleware):
        """403 response should NOT include CORS headers for disallowed origins."""
        disallowed_origin = "https://evil.example.com"
        request = make_request(
            "POST",
            "/api/v1/bookings",
            cookies={},
            headers={"origin": disallowed_origin},
        )

        with patch("core.csrf_middleware.is_origin_allowed", return_value=False):
            response = await middleware.dispatch(
                request, lambda r: AsyncMock(return_value=Response())()
            )

        assert response.status_code == 403
        assert "access-control-allow-origin" not in response.headers


class TestCSRFMiddlewareWebSocketBypass:
    """Tests for WebSocket upgrade bypass (BaseHTTPMiddleware breaks on WebSocket)."""

    @pytest.mark.asyncio
    async def test_websocket_scope_bypasses_middleware(self, mock_app):
        """WebSocket scope should pass through to app without CSRF middleware."""
        scope = {"type": "websocket", "headers": []}
        receive = AsyncMock()
        send = AsyncMock()

        middleware = CSRFMiddleware(mock_app)
        await middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_websocket_upgrade_http_request_bypasses_middleware(self, mock_app):
        """HTTP request with Upgrade: websocket should pass through to app."""
        scope = {
            "type": "http",
            "headers": [[b"upgrade", b"websocket"], [b"connection", b"Upgrade"]],
        }
        receive = AsyncMock()
        send = AsyncMock()

        middleware = CSRFMiddleware(mock_app)
        await middleware(scope, receive, send)

        mock_app.assert_called_once_with(scope, receive, send)

    def test_is_websocket_upgrade_websocket_scope(self):
        """_is_websocket_upgrade returns True for websocket scope."""
        assert _is_websocket_upgrade({"type": "websocket"}) is True

    def test_is_websocket_upgrade_http_with_upgrade_header(self):
        """_is_websocket_upgrade returns True for HTTP with Upgrade: websocket."""
        scope = {"type": "http", "headers": [[b"upgrade", b"websocket"]]}
        assert _is_websocket_upgrade(scope) is True

    def test_is_websocket_upgrade_http_without_upgrade(self):
        """_is_websocket_upgrade returns False for normal HTTP."""
        scope = {"type": "http", "headers": [[b"content-type", b"application/json"]]}
        assert _is_websocket_upgrade(scope) is False


class TestCSRFMiddlewareConfiguration:
    """Tests for middleware configuration."""

    @pytest.mark.asyncio
    async def test_empty_exempt_paths(self, mock_app):
        """Middleware should work with no exempt paths."""
        middleware = CSRFMiddleware(mock_app)
        request = make_request("POST", "/api/v1/anything", cookies={}, headers={})
        response = await middleware.dispatch(
            request, lambda r: AsyncMock(return_value=Response())()
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_multiple_exempt_paths(self, mock_app):
        """Middleware should handle multiple exempt paths."""
        middleware = CSRFMiddleware(
            mock_app,
            exempt_paths=[
                "/api/v1/auth/login",
                "/api/v1/auth/register",
                "/api/v1/webhooks/*",
            ],
        )

        # Test each exempt path
        for path in ["/api/v1/auth/login", "/api/v1/auth/register"]:
            request = make_request("POST", path)
            inner_called = False

            async def call_next(req):
                nonlocal inner_called
                inner_called = True
                return Response()

            await middleware.dispatch(request, call_next)
            assert inner_called, f"Path {path} should be exempt"
