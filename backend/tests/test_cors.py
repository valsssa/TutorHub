"""
CORS Configuration Tests

These tests verify that CORS is properly configured and working for all scenarios:
1. Preflight (OPTIONS) requests
2. Simple requests from allowed origins
3. Requests from disallowed origins
4. Error responses include CORS headers
5. Rate limit responses include CORS headers
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    """Create test client with test environment."""
    import os
    os.environ["ENVIRONMENT"] = "development"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://allowed-origin.com"
    os.environ["SKIP_STARTUP_MIGRATIONS"] = "true"

    from main import app
    return TestClient(app)


class TestCORSPreflight:
    """Test OPTIONS preflight requests."""

    def test_preflight_from_allowed_origin(self, client):
        """OPTIONS request from allowed origin should return 200/204 with CORS headers."""
        response = client.options(
            "/api/v1/cors-test",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # Should succeed (200 or 204)
        assert response.status_code in [200, 204]

        # Must have CORS headers
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"
        assert "GET" in response.headers.get("Access-Control-Allow-Methods", "")
        assert "Authorization" in response.headers.get("Access-Control-Allow-Headers", "")

    def test_preflight_from_disallowed_origin(self, client):
        """OPTIONS request from disallowed origin should not have Access-Control-Allow-Origin."""
        response = client.options(
            "/api/v1/cors-test",
            headers={
                "Origin": "http://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Response should not include the evil origin
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        assert allow_origin != "http://evil.com"
        assert allow_origin != "*"


class TestCORSSimpleRequests:
    """Test regular (non-preflight) requests."""

    def test_get_from_allowed_origin(self, client):
        """GET request from allowed origin should have CORS headers."""
        response = client.get(
            "/api/v1/cors-test",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_get_from_disallowed_origin(self, client):
        """GET request from disallowed origin should not have Access-Control-Allow-Origin for that origin."""
        response = client.get(
            "/api/v1/cors-test",
            headers={"Origin": "http://evil.com"},
        )

        # Request should succeed (no server-side blocking)
        assert response.status_code == 200

        # But CORS header should not be set for evil origin
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        assert allow_origin != "http://evil.com"

    def test_cors_test_endpoint_returns_debug_info(self, client):
        """CORS test endpoint should return useful debugging information."""
        response = client.get(
            "/api/v1/cors-test",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "cors_debug" in data
        assert "request" in data["cors_debug"]
        assert "configuration" in data["cors_debug"]
        assert data["cors_debug"]["request"]["origin"] == "http://localhost:3000"
        assert data["cors_debug"]["configuration"]["origin_allowed"] is True


class TestCORSErrorResponses:
    """Test that error responses include CORS headers."""

    def test_404_includes_cors_headers(self, client):
        """404 responses should include CORS headers."""
        response = client.get(
            "/api/v1/nonexistent-endpoint-12345",
            headers={"Origin": "http://localhost:3000"},
        )

        assert response.status_code == 404
        # CORS headers should be present even on error
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_health_endpoint_works_without_cors(self, client):
        """Health endpoint should work without Origin header."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCORSOriginValidation:
    """Test origin validation logic."""

    def test_case_insensitive_origin_matching(self, client):
        """Origin matching should be case-insensitive."""
        response = client.get(
            "/api/v1/cors-test",
            headers={"Origin": "HTTP://LOCALHOST:3000"},
        )

        assert response.status_code == 200
        # Should match despite different case
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        assert allow_origin.lower() == "http://localhost:3000"

    def test_origin_with_trailing_slash_handled(self, client):
        """Origin with trailing slash should be handled correctly.

        The server should match origins after normalizing them, meaning
        http://localhost:3000/ should match http://localhost:3000.
        The returned Access-Control-Allow-Origin can be either form.
        """
        response = client.get(
            "/api/v1/cors-test",
            headers={"Origin": "http://localhost:3000/"},
        )

        assert response.status_code == 200
        # Should match after normalization - either with or without trailing slash
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        # Either normalized form (without /) or original form (with /) is valid
        assert allow_origin in ["http://localhost:3000", "http://localhost:3000/"]


class TestCORSConfiguration:
    """Test CORS configuration utilities."""

    def test_get_cors_origins_from_env(self):
        """get_cors_origins should parse CORS_ORIGINS environment variable."""
        import os
        from core.cors import get_cors_origins

        os.environ["CORS_ORIGINS"] = "http://test1.com,http://test2.com,invalid"
        origins = get_cors_origins()

        assert "http://test1.com" in origins
        assert "http://test2.com" in origins
        # Invalid entries (no http/https) should be filtered
        assert "invalid" not in origins

    def test_get_cors_headers(self):
        """get_cors_headers should return proper headers for allowed origin."""
        from core.cors import get_cors_headers

        headers = get_cors_headers(
            origin="http://localhost:3000",
            allowed_origins=["http://localhost:3000", "http://other.com"],
        )

        assert headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
        assert headers["Access-Control-Allow-Credentials"] == "true"
        assert "GET" in headers["Access-Control-Allow-Methods"]
        assert "Authorization" in headers["Access-Control-Allow-Headers"]

    def test_get_cors_headers_disallowed_origin(self):
        """get_cors_headers should return empty dict for disallowed origin."""
        from core.cors import get_cors_headers

        headers = get_cors_headers(
            origin="http://evil.com",
            allowed_origins=["http://localhost:3000"],
        )

        assert headers == {}


class TestCORSExceptionHandlers:
    """Test that exception handlers include CORS headers."""

    def test_http_exception_handler_includes_cors(self):
        """HTTPException handler should include CORS headers."""
        from fastapi import HTTPException, Request
        from core.cors import create_cors_http_exception_handler
        from starlette.testclient import TestClient
        from fastapi import FastAPI
        import asyncio

        app = FastAPI()
        handler = create_cors_http_exception_handler(["http://test.com"])

        @app.get("/test")
        async def raise_error():
            raise HTTPException(status_code=400, detail="Test error")

        app.add_exception_handler(HTTPException, handler)
        client = TestClient(app)

        response = client.get("/test", headers={"Origin": "http://test.com"})

        assert response.status_code == 400
        assert response.headers.get("Access-Control-Allow-Origin") == "http://test.com"

    def test_rate_limit_handler_includes_cors(self):
        """Rate limit handler should include CORS headers."""
        from core.cors import create_cors_rate_limit_handler
        from fastapi import FastAPI, Request
        from starlette.testclient import TestClient
        from slowapi.errors import RateLimitExceeded
        from slowapi.wrappers import Limit
        from unittest.mock import MagicMock

        app = FastAPI()
        handler = create_cors_rate_limit_handler(["http://test.com"])

        # Create a mock Limit object for RateLimitExceeded
        mock_limit = MagicMock()
        mock_limit.limit = "10/minute"
        mock_limit.error_message = None

        @app.get("/test")
        async def rate_limited():
            raise RateLimitExceeded(mock_limit)

        app.add_exception_handler(RateLimitExceeded, handler)
        client = TestClient(app)

        response = client.get("/test", headers={"Origin": "http://test.com"})

        assert response.status_code == 429
        assert response.headers.get("Access-Control-Allow-Origin") == "http://test.com"
        assert "Retry-After" in response.headers


class TestCORSMiddleware:
    """Test CORSErrorMiddleware."""

    def test_cors_error_middleware_adds_missing_headers(self):
        """CORSErrorMiddleware should add CORS headers if missing."""
        from core.cors import CORSErrorMiddleware
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        from starlette.testclient import TestClient
        import os

        os.environ["CORS_ORIGINS"] = "http://test.com"

        app = FastAPI()
        app.add_middleware(CORSErrorMiddleware)

        @app.get("/test")
        async def test_endpoint():
            # Return response without CORS headers
            return JSONResponse(content={"test": "data"})

        client = TestClient(app)
        response = client.get("/test", headers={"Origin": "http://test.com"})

        assert response.status_code == 200
        # Middleware should have added CORS headers
        assert response.headers.get("Access-Control-Allow-Origin") == "http://test.com"
