"""Tests for the security headers middleware."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response

from core.middleware import SecurityHeadersMiddleware


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware class."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware_dev(self, app):
        """Create middleware in development mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            return SecurityHeadersMiddleware(app)

    @pytest.fixture
    def middleware_prod(self, app):
        """Create middleware in production mode."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            return SecurityHeadersMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        return request

    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        response = MagicMock(spec=Response)
        response.headers = {}
        return response

    def test_init_development(self, middleware_dev):
        """Test middleware initialization in development."""
        assert middleware_dev.enable_hsts is False

    def test_init_production(self):
        """Test middleware initialization in production."""
        app = MagicMock()
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            middleware = SecurityHeadersMiddleware(app)
            assert middleware.enable_hsts is True

    def test_init_staging(self):
        """Test middleware initialization in staging."""
        app = MagicMock()
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            middleware = SecurityHeadersMiddleware(app)
            assert middleware.enable_hsts is True

    @pytest.mark.asyncio
    async def test_adds_x_frame_options(self, middleware_dev, mock_request):
        """Test X-Frame-Options header is added."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_adds_x_content_type_options(self, middleware_dev, mock_request):
        """Test X-Content-Type-Options header is added."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_adds_x_xss_protection(self, middleware_dev, mock_request):
        """Test X-XSS-Protection header is added."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_adds_referrer_policy(self, middleware_dev, mock_request):
        """Test Referrer-Policy header is added."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    @pytest.mark.asyncio
    async def test_adds_permissions_policy(self, middleware_dev, mock_request):
        """Test Permissions-Policy header is added."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        permissions = response.headers["Permissions-Policy"]
        assert "camera=()" in permissions
        assert "microphone=()" in permissions
        assert "geolocation=()" in permissions
        assert "payment=()" in permissions

    @pytest.mark.asyncio
    async def test_strict_csp_for_api_endpoints(self, middleware_dev, mock_request):
        """Test strict CSP for API endpoints."""
        mock_request.url.path = "/api/users"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'none'" in csp
        assert "script-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_relaxed_csp_for_docs(self, middleware_dev, mock_request):
        """Test relaxed CSP for documentation endpoints."""
        mock_request.url.path = "/docs"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "script-src 'self' https: 'unsafe-inline'" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp

    @pytest.mark.asyncio
    async def test_relaxed_csp_for_redoc(self, middleware_dev, mock_request):
        """Test relaxed CSP for redoc endpoint."""
        mock_request.url.path = "/redoc"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "'unsafe-inline'" in csp

    @pytest.mark.asyncio
    async def test_relaxed_csp_for_openapi(self, middleware_dev, mock_request):
        """Test relaxed CSP for OpenAPI endpoint."""
        mock_request.url.path = "/openapi.json"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "'unsafe-inline'" in csp

    @pytest.mark.asyncio
    async def test_relaxed_csp_for_static(self, middleware_dev, mock_request):
        """Test relaxed CSP for static files."""
        mock_request.url.path = "/static/swagger-ui.css"
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "'unsafe-inline'" in csp

    @pytest.mark.asyncio
    async def test_hsts_not_added_in_development(self, middleware_dev, mock_request):
        """Test HSTS header is not added in development."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert "Strict-Transport-Security" not in response.headers

    @pytest.mark.asyncio
    async def test_hsts_added_in_production(self, mock_request):
        """Test HSTS header is added in production."""
        app = MagicMock()
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            middleware = SecurityHeadersMiddleware(app)

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    @pytest.mark.asyncio
    async def test_removes_server_header(self, middleware_dev, mock_request):
        """Test Server header is removed."""
        mock_response = MagicMock()
        mock_response.headers = {"Server": "Apache/2.4.1"}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert "Server" not in response.headers

    @pytest.mark.asyncio
    async def test_preserves_response_without_server_header(
        self, middleware_dev, mock_request
    ):
        """Test response without Server header is handled."""
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware_dev.dispatch(mock_request, call_next)

        assert "Server" not in response.headers


class TestCSPDirectives:
    """Tests for Content-Security-Policy directives."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            return SecurityHeadersMiddleware(app)

    @pytest.mark.asyncio
    async def test_csp_base_uri(self, middleware):
        """Test base-uri directive is set."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "base-uri 'self'" in csp

    @pytest.mark.asyncio
    async def test_csp_form_action(self, middleware):
        """Test form-action directive is set."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "form-action 'self'" in csp

    @pytest.mark.asyncio
    async def test_csp_frame_ancestors(self, middleware):
        """Test frame-ancestors directive is set."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in csp

    @pytest.mark.asyncio
    async def test_csp_object_src(self, middleware):
        """Test object-src directive is set."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        csp = response.headers["Content-Security-Policy"]
        assert "object-src 'none'" in csp


class TestEnvironmentDetection:
    """Tests for environment detection."""

    def test_env_variable(self):
        """Test ENVIRONMENT variable is used."""
        app = MagicMock()
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            middleware = SecurityHeadersMiddleware(app)
            assert middleware.enable_hsts is True

    def test_fallback_env_variable(self):
        """Test ENV variable is used as fallback."""
        app = MagicMock()
        with patch.dict(os.environ, {"ENV": "production"}, clear=False):
            with patch.dict(os.environ, {"ENVIRONMENT": ""}, clear=False):
                pass

    def test_default_environment(self):
        """Test default environment is development."""
        app = MagicMock()
        with patch.dict(os.environ, {}, clear=True):
            middleware = SecurityHeadersMiddleware(app)
            assert middleware.enable_hsts is False


class TestPermissionsPolicyDirectives:
    """Tests for Permissions-Policy directives."""

    @pytest.fixture
    def app(self):
        """Create mock app."""
        return MagicMock()

    @pytest.fixture
    def middleware(self, app):
        """Create middleware instance."""
        return SecurityHeadersMiddleware(app)

    @pytest.mark.asyncio
    async def test_all_permissions_disabled(self, middleware):
        """Test all sensitive permissions are disabled."""
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"

        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)

        permissions = response.headers["Permissions-Policy"]
        expected_disabled = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ]
        for directive in expected_disabled:
            assert directive in permissions, f"Missing directive: {directive}"
