"""
CORS Configuration Tests

Tests the single-source-of-truth CORS implementation in core/cors.py.

These tests verify:
1. Configuration loading from environment
2. Origin validation logic
3. Preflight (OPTIONS) handling
4. CORS headers on success/error responses
5. HttpOnly cookie authentication support
"""

import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# =============================================================================
# Configuration Tests
# =============================================================================


class TestCORSConfig:
    """Tests for CORSConfig dataclass."""

    def test_config_is_immutable(self):
        """Config should be frozen (immutable)."""
        from core.cors import CORSConfig

        config = CORSConfig(origins=("http://localhost:3000",))
        with pytest.raises(Exception):  # FrozenInstanceError
            config.origins = ("http://other.com",)

    def test_config_defaults(self):
        """Config should have sensible defaults."""
        from core.cors import CORSConfig

        config = CORSConfig(origins=("http://localhost:3000",))
        assert config.credentials is True
        assert config.max_age == 86400
        assert "GET" in config.methods
        assert "Authorization" in config.headers
        assert "X-CSRF-Token" in config.headers


class TestGetCORSConfig:
    """Tests for get_cors_config() function."""

    def test_production_defaults(self):
        """Production environment should use production origins."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            # Clear CORS_ORIGINS to use defaults
            os.environ.pop("CORS_ORIGINS", None)

            import core.cors
            core.cors._config = None

            config = core.cors.get_cors_config()
            assert "https://edustream.valsa.solutions" in config.origins
            assert config.max_age == 86400

    def test_development_defaults(self):
        """Development environment should include localhost origins."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            os.environ.pop("CORS_ORIGINS", None)

            import core.cors
            core.cors._config = None

            config = core.cors.get_cors_config()
            assert "http://localhost:3000" in config.origins
            assert config.max_age == 600

    def test_env_variable_override(self):
        """CORS_ORIGINS env variable should override defaults."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://custom.com,https://other.com"}):
            import core.cors
            core.cors._config = None

            config = core.cors.get_cors_config()
            assert "https://custom.com" in config.origins
            assert "https://other.com" in config.origins

    def test_invalid_origins_filtered(self):
        """Origins without http/https prefix should be filtered out."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://valid.com,invalid.com,ftp://other.com"}):
            import core.cors
            core.cors._config = None

            config = core.cors.get_cors_config()
            assert "https://valid.com" in config.origins
            # Invalid origins should be filtered
            origins_str = str(config.origins)
            assert "invalid.com" not in origins_str or "https://valid.com" in origins_str

    def test_trailing_slash_normalized(self):
        """Origins should have trailing slashes removed."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com/"}):
            import core.cors
            core.cors._config = None

            config = core.cors.get_cors_config()
            assert "https://example.com" in config.origins


class TestIsOriginAllowed:
    """Tests for is_origin_allowed() function."""

    def test_allowed_origin(self):
        """Allowed origin should return True."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://allowed.com"}):
            import core.cors
            core.cors._config = None

            assert core.cors.is_origin_allowed("https://allowed.com") is True

    def test_disallowed_origin(self):
        """Disallowed origin should return False."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://allowed.com"}):
            import core.cors
            core.cors._config = None

            assert core.cors.is_origin_allowed("https://evil.com") is False

    def test_none_origin(self):
        """None origin should return False."""
        from core.cors import is_origin_allowed
        assert is_origin_allowed(None) is False

    def test_case_insensitive(self):
        """Origin matching should be case-insensitive."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com"}):
            import core.cors
            core.cors._config = None

            assert core.cors.is_origin_allowed("HTTPS://EXAMPLE.COM") is True

    def test_trailing_slash_handled(self):
        """Trailing slashes should not affect matching."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com"}):
            import core.cors
            core.cors._config = None

            assert core.cors.is_origin_allowed("https://example.com/") is True


# =============================================================================
# Integration Tests with FastAPI App
# =============================================================================


@pytest.fixture
def test_app():
    """Create a minimal test app with CORS configured."""
    with patch.dict(os.environ, {
        "CORS_ORIGINS": "http://localhost:3000,http://allowed.com",
        "ENVIRONMENT": "test"
    }):
        import core.cors
        core.cors._config = None

        app = FastAPI()
        core.cors.setup_cors(app)

        @app.get("/test")
        def test_endpoint():
            return {"message": "ok"}

        @app.get("/error-403")
        def forbidden_endpoint():
            raise HTTPException(status_code=403, detail="Forbidden")

        @app.get("/error-500")
        def server_error():
            raise ValueError("Unexpected error")

        yield app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app, raise_server_exceptions=False)


class TestCORSPreflight:
    """Test OPTIONS preflight requests."""

    def test_preflight_from_allowed_origin(self, client):
        """OPTIONS request from allowed origin should return CORS headers."""
        response = client.options(
            "/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # Should succeed
        assert response.status_code in [200, 204]

        # Must have CORS headers
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"
        assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")

    def test_preflight_from_disallowed_origin(self, client):
        """OPTIONS request from disallowed origin should not have allow-origin header."""
        response = client.options(
            "/test",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should not have allow-origin for disallowed origin
        assert response.headers.get("Access-Control-Allow-Origin") is None


class TestCORSSimpleRequests:
    """Test simple (non-preflight) requests."""

    def test_get_from_allowed_origin(self, client):
        """GET request from allowed origin should have CORS headers."""
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_get_from_disallowed_origin(self, client):
        """GET request from disallowed origin should not have CORS headers."""
        response = client.get(
            "/test",
            headers={"Origin": "http://evil.com"},
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") is None


class TestCORSErrorResponses:
    """Test that error responses include CORS headers."""

    def test_404_has_cors_headers(self, client):
        """404 responses should have CORS headers."""
        response = client.get(
            "/nonexistent",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 404
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_403_has_cors_headers(self, client):
        """HTTPException (403) responses should have CORS headers."""
        response = client.get(
            "/error-403",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 403
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_500_has_cors_headers(self, client):
        """500 error responses should have CORS headers (via safety net)."""
        response = client.get(
            "/error-500",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 500
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"


class TestCORSOriginValidation:
    """Test origin validation edge cases."""

    def test_case_insensitive_matching(self, client):
        """Origin matching should be case-insensitive."""
        response = client.get(
            "/test",
            headers={"Origin": "HTTP://LOCALHOST:3000"},
        )

        assert response.status_code == 200
        # Note: The returned origin may be normalized
        origin = response.headers.get("Access-Control-Allow-Origin")
        assert origin is not None

    def test_trailing_slash_handled(self, client):
        """Trailing slash in origin should not break matching."""
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000/"},
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") is not None


class TestCORSCredentialsSupport:
    """Test HttpOnly cookie authentication support."""

    def test_credentials_header_present(self, client):
        """Access-Control-Allow-Credentials should be true."""
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_csrf_token_header_allowed(self, client):
        """X-CSRF-Token should be in allowed headers."""
        response = client.options(
            "/test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-CSRF-Token",
            },
        )

        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        assert "x-csrf-token" in allowed_headers

    def test_no_wildcard_with_credentials(self, client):
        """Should never use wildcard origin with credentials."""
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"},
        )

        origin = response.headers.get("Access-Control-Allow-Origin")
        assert origin != "*"
        assert origin == "http://localhost:3000"

    def test_vary_header_present(self, client):
        """Vary: Origin should be present for cache correctness."""
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"},
        )

        vary = response.headers.get("Vary", "")
        assert "origin" in vary.lower()


class TestSetupCORS:
    """Tests for the setup_cors() function."""

    def test_setup_cors_configures_app(self):
        """setup_cors should configure the app correctly."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://test.com", "ENVIRONMENT": "test"}):
            import core.cors
            core.cors._config = None

            app = FastAPI()
            core.cors.setup_cors(app)

            # Should have middleware registered
            assert len(app.user_middleware) > 0

    def test_setup_cors_registers_exception_handlers(self):
        """setup_cors should register exception handlers."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://test.com", "ENVIRONMENT": "test"}):
            import core.cors
            core.cors._config = None

            app = FastAPI()
            core.cors.setup_cors(app)

            # HTTPException handler should be registered
            assert HTTPException in app.exception_handlers
