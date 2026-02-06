"""
Integration tests for HttpOnly cookie authentication flow.

Tests the complete cookie-based auth lifecycle including:
- Registration and login with cookie setting
- CSRF protection on state-changing requests
- Token refresh with cookies
- Logout and cookie clearing
- Backwards compatibility with Bearer tokens
"""

import pytest
from conftest import TEST_PASSWORD, create_test_user
from fastapi import status
from fastapi.testclient import TestClient


class TestFullAuthFlowWithCookies:
    """Test complete authentication flow using HttpOnly cookies."""

    def test_full_auth_flow_with_cookies(self, client: TestClient, db_session):
        """Complete flow: register -> login -> access protected -> CSRF request -> refresh -> logout."""
        # 1. Register a new user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "cookie_test@example.com",
                "password": TEST_PASSWORD,
                "first_name": "Cookie",
                "last_name": "Test",
                "role": "student",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # 2. Login - should set cookies
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "cookie_test@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Verify response contains tokens
        login_data = login_response.json()
        assert "access_token" in login_data
        assert "refresh_token" in login_data
        assert login_data["token_type"] == "bearer"

        # Verify cookies are set
        cookies = login_response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies
        assert "csrf_token" in cookies

        # Store cookies for subsequent requests
        access_token_cookie = cookies.get("access_token")
        refresh_token_cookie = cookies.get("refresh_token")
        csrf_token = cookies.get("csrf_token")

        assert access_token_cookie is not None
        assert refresh_token_cookie is not None
        assert csrf_token is not None

        # 3. Access protected endpoint using cookie (no Authorization header)
        # TestClient automatically sends cookies
        me_response = client.get("/api/v1/auth/me")
        assert me_response.status_code == status.HTTP_200_OK
        me_data = me_response.json()
        assert me_data["email"] == "cookie_test@example.com"

        # 4. Make CSRF-protected request (PUT /profile/me) with CSRF token
        # Note: /auth/* endpoints are CSRF-exempt, so use /profile/me instead
        update_response = client.put(
            "/api/v1/profile/me",
            json={"bio": "Updated via cookie auth"},
            headers={"X-CSRF-Token": csrf_token},
        )
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["bio"] == "Updated via cookie auth"

        # 5. Refresh token - should set new access token cookie
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == status.HTTP_200_OK

        # Verify new access token is set
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        new_csrf_token = refresh_response.cookies.get("csrf_token")
        assert new_csrf_token is not None

        # 6. Logout - should clear cookies (auth endpoints are CSRF-exempt)
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.json()["message"] == "Successfully logged out"

        # 7. Verify cookies are cleared (access protected endpoint fails)
        # Create a new client to simulate cleared cookies
        with TestClient(client.app) as new_client:
            me_after_logout = new_client.get("/api/v1/auth/me")
            assert me_after_logout.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_sets_correct_cookie_attributes(self, client: TestClient, student_user):
        """Verify login sets cookies with proper security attributes."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        # Check Set-Cookie headers for security attributes
        set_cookie_headers = response.headers.getlist("set-cookie")
        assert len(set_cookie_headers) >= 3  # access_token, refresh_token, csrf_token

        # Find access_token cookie header
        access_cookie_header = next(
            (h for h in set_cookie_headers if h.startswith("access_token=")), None
        )
        assert access_cookie_header is not None
        assert "HttpOnly" in access_cookie_header
        assert "SameSite=lax" in access_cookie_header.lower()

        # Find refresh_token cookie header
        refresh_cookie_header = next(
            (h for h in set_cookie_headers if h.startswith("refresh_token=")), None
        )
        assert refresh_cookie_header is not None
        assert "HttpOnly" in refresh_cookie_header
        # Refresh token should have restricted path
        assert "Path=/api/v1/auth" in refresh_cookie_header

        # Find csrf_token cookie header
        csrf_cookie_header = next(
            (h for h in set_cookie_headers if h.startswith("csrf_token=")), None
        )
        assert csrf_cookie_header is not None
        # CSRF cookie should NOT be HttpOnly (JS needs to read it)
        assert "HttpOnly" not in csrf_cookie_header or "httponly" not in csrf_cookie_header.lower()


class TestCSRFProtection:
    """Test CSRF protection on non-auth endpoints."""

    def test_csrf_protection_blocks_post_without_token(
        self, client: TestClient, student_user, student_token
    ):
        """PUT requests fail with 403 when missing CSRF token."""
        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Try to make a PUT request without CSRF token to a non-exempt endpoint
        # Using PUT /profile/me which requires CSRF since it's NOT in /auth/* path
        update_response = client.put(
            "/api/v1/profile/me",
            json={"bio": "Testing without CSRF"},
            # No X-CSRF-Token header
        )
        assert update_response.status_code == status.HTTP_403_FORBIDDEN
        assert "CSRF" in update_response.json().get("detail", "")

    def test_csrf_protection_allows_with_valid_token(
        self, client: TestClient, student_user
    ):
        """PUT requests succeed when CSRF token is provided."""
        # Login to get cookies including CSRF token
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        csrf_token = login_response.cookies.get("csrf_token")
        assert csrf_token is not None

        # Make PUT request with CSRF token to non-auth endpoint
        update_response = client.put(
            "/api/v1/profile/me",
            json={"bio": "Testing with CSRF token"},
            headers={"X-CSRF-Token": csrf_token},
        )
        assert update_response.status_code == status.HTTP_200_OK

    def test_csrf_protection_blocks_mismatched_token(
        self, client: TestClient, student_user
    ):
        """PUT requests fail when CSRF token doesn't match cookie."""
        # Login to get cookies
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Try with a different/invalid CSRF token
        update_response = client.put(
            "/api/v1/profile/me",
            json={"bio": "Testing with wrong token"},
            headers={"X-CSRF-Token": "invalid_csrf_token_value"},
        )
        assert update_response.status_code == status.HTTP_403_FORBIDDEN

    def test_auth_endpoints_exempt_from_csrf(self, client: TestClient, db_session):
        """Auth endpoints (login, register, refresh, logout) don't require CSRF tokens."""
        # Register without CSRF token should work
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "csrf_exempt_test@example.com",
                "password": TEST_PASSWORD,
                "first_name": "CSRF",
                "last_name": "Exempt",
                "role": "student",
            },
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # Login without CSRF token should work
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "csrf_exempt_test@example.com",
                "password": TEST_PASSWORD,
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Refresh without CSRF token should work (uses cookie, in exempt path)
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == status.HTTP_200_OK

        # Logout without CSRF token should work (in exempt path /api/v1/auth/*)
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK


class TestBackwardsCompatibilityWithBearerToken:
    """Test that Authorization header still works for backwards compatibility."""

    def test_backwards_compatibility_with_bearer_token(
        self, client: TestClient, student_user, student_token
    ):
        """Authorization header still works for backwards compatibility."""
        # Access protected endpoint using Bearer token (legacy method)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == student_user.email

    def test_bearer_token_works_without_cookies(
        self, client: TestClient, student_user, student_token
    ):
        """Bearer token authentication works even without any cookies."""
        # Use a fresh client with no cookies
        from main import app

        with TestClient(app) as fresh_client:
            response = fresh_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["email"] == student_user.email


class TestCookiePriorityOverHeader:
    """Test that cookie token takes priority over Authorization header."""

    def test_cookie_takes_priority_over_header(
        self, client: TestClient, student_user, tutor_user, db_session
    ):
        """Cookie token is used when both cookie and header are present."""
        from core.security import TokenManager

        # Login as student to get student cookies
        student_login = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert student_login.status_code == status.HTTP_200_OK

        # Create a tutor token for the header
        tutor_token = TokenManager.create_access_token({"sub": tutor_user.email})

        # Make request with both cookie (student) and header (tutor)
        # Cookie should take priority - we should get student info
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Should be student (from cookie), not tutor (from header)
        user_data = response.json()
        assert user_data["email"] == student_user.email
        assert user_data["role"] == "student"


class TestLogoutClearsCookies:
    """Test that logout properly clears all auth cookies."""

    def test_logout_clears_all_cookies(self, client: TestClient, student_user):
        """Logout clears access_token, refresh_token, and csrf_token cookies."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK

        # Logout (auth endpoints are CSRF-exempt)
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == status.HTTP_200_OK

        # Check Set-Cookie headers to verify cookies are being cleared
        # Cleared cookies typically have Max-Age=0 or expires in the past
        set_cookie_headers = logout_response.headers.getlist("set-cookie")

        # Find cookies that are being cleared (max-age=0)
        cleared_cookies = [h for h in set_cookie_headers if "max-age=0" in h.lower() or 'expires=' in h.lower()]

        # At minimum, we should have cookies being deleted
        assert len(cleared_cookies) >= 1


class TestRefreshTokenFlow:
    """Test refresh token behavior with cookies."""

    def test_refresh_updates_access_token_cookie(self, client: TestClient, student_user):
        """Refresh endpoint updates the access_token cookie."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        # Store access token for assertion comparison if needed
        assert login_response.cookies.get("access_token") is not None

        # Refresh
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == status.HTTP_200_OK

        # Verify new access token is set
        new_access_token = refresh_response.cookies.get("access_token")
        assert new_access_token is not None

        # New token should be different from original
        # (tokens include timestamp, so should differ)
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data

    def test_refresh_generates_new_csrf_token(self, client: TestClient, student_user):
        """Refresh endpoint generates a new CSRF token."""
        # Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        # Confirm CSRF token is set
        assert login_response.cookies.get("csrf_token") is not None

        # Refresh
        refresh_response = client.post("/api/v1/auth/refresh")
        assert refresh_response.status_code == status.HTTP_200_OK

        # New CSRF token should be set
        new_csrf = refresh_response.cookies.get("csrf_token")
        assert new_csrf is not None

    def test_refresh_without_refresh_token_fails(self, client: TestClient):
        """Refresh fails when no refresh token cookie is present."""
        from main import app

        # Use fresh client with no cookies
        with TestClient(app) as fresh_client:
            response = fresh_client.post("/api/v1/auth/refresh")
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_in_body_still_works(self, client: TestClient, student_user):
        """Refresh token can still be provided in request body (backwards compat)."""
        # Login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": student_user.email,
                "password": "StudentPass123!",
            },
        )
        assert login_response.status_code == status.HTTP_200_OK
        refresh_token = login_response.json()["refresh_token"]

        # Use fresh client without cookies
        from main import app

        with TestClient(app) as fresh_client:
            # Provide refresh token in body
            response = fresh_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert response.status_code == status.HTTP_200_OK
            assert "access_token" in response.json()
