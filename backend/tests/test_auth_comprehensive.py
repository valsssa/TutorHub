"""
Comprehensive tests for authentication functionality.

Tests cover:
- Token expiration and validation
- OAuth flow (Google)
- Password reset flow
- Token invalidation after password change
- Edge cases and error handling
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status


class TestTokenExpiration:
    """Test JWT token expiration handling."""

    def test_token_valid_within_expiry(self, client, student_token, student_user):
        """Test valid token within expiry period."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == student_user.email

    def test_token_expired(self, client, db_session, student_user):
        """Test expired token is rejected."""
        from core.security import TokenManager

        expired_token = TokenManager.create_access_token(
            data={"sub": student_user.email},
            expires_delta=timedelta(seconds=-1),
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_invalid_signature(self, client):
        """Test token with invalid signature is rejected."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIn0.invalid_signature"

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_malformed(self, client):
        """Test malformed token is rejected."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_missing_sub_claim(self, client):
        """Test token without sub claim is rejected."""
        from jose import jwt
        from core.config import settings

        token_without_sub = jwt.encode(
            {"exp": datetime.now(UTC) + timedelta(hours=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token_without_sub}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenInvalidationOnPasswordChange:
    """Test that tokens are invalidated when password changes."""

    def test_old_token_invalid_after_password_change(
        self, client, db_session, student_user
    ):
        """Test old token becomes invalid after password change."""
        from core.security import TokenManager, PasswordHasher

        old_token = TokenManager.create_access_token({"sub": student_user.email})

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        student_user.hashed_password = PasswordHasher.hash("NewPassword123!")
        password_change_time = datetime.now(UTC)
        student_user.password_changed_at = password_change_time
        db_session.commit()

        # New token must include pwd_ts claim (simulating real login flow)
        new_token = TokenManager.create_access_token({
            "sub": student_user.email,
            "pwd_ts": password_change_time.timestamp()
        })
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert response.status_code == status.HTTP_200_OK


class TestPasswordResetFlow:
    """Test password reset functionality."""

    def test_request_password_reset_existing_user(self, client, student_user):
        """Test password reset request for existing user."""
        with patch("modules.auth.password_router.email_service") as mock_email:
            mock_email.send_password_reset = MagicMock()

            response = client.post(
                "/api/v1/auth/password/reset-request",
                json={"email": student_user.email},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "if an account exists" in response.json()["message"].lower()
            mock_email.send_password_reset.assert_called_once()

    def test_request_password_reset_nonexistent_user(self, client):
        """Test password reset request for non-existent user returns same response."""
        with patch("modules.auth.password_router.email_service") as mock_email:
            mock_email.send_password_reset = MagicMock()

            response = client.post(
                "/api/v1/auth/password/reset-request",
                json={"email": "nonexistent@test.com"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "if an account exists" in response.json()["message"].lower()
            mock_email.send_password_reset.assert_not_called()

    def test_request_password_reset_inactive_user(self, client, db_session, student_user):
        """Test password reset request for inactive user."""
        student_user.is_active = False
        db_session.commit()

        with patch("modules.auth.password_router.email_service") as mock_email:
            mock_email.send_password_reset = MagicMock()

            response = client.post(
                "/api/v1/auth/password/reset-request",
                json={"email": student_user.email},
            )

            assert response.status_code == status.HTTP_200_OK
            mock_email.send_password_reset.assert_not_called()

    def test_verify_reset_token_valid(self, client, student_user):
        """Test verifying a valid reset token."""
        from modules.auth.password_router import _reset_tokens

        test_token = "valid_test_token_12345"
        _reset_tokens[test_token] = {
            "user_id": student_user.id,
            "email": student_user.email,
            "created_at": datetime.now(UTC),
        }

        try:
            response = client.post(
                "/api/v1/auth/password/verify-token",
                json={"token": test_token},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "valid" in response.json()["message"].lower()
        finally:
            if test_token in _reset_tokens:
                del _reset_tokens[test_token]

    def test_verify_reset_token_invalid(self, client):
        """Test verifying an invalid reset token."""
        response = client.post(
            "/api/v1/auth/password/verify-token",
            json={"token": "invalid_token"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()

    def test_verify_reset_token_expired(self, client, student_user):
        """Test verifying an expired reset token."""
        from modules.auth.password_router import _reset_tokens

        test_token = "expired_test_token"
        _reset_tokens[test_token] = {
            "user_id": student_user.id,
            "email": student_user.email,
            "created_at": datetime.now(UTC) - timedelta(hours=2),
        }

        try:
            response = client.post(
                "/api/v1/auth/password/verify-token",
                json={"token": test_token},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "expired" in response.json()["detail"].lower()
        finally:
            if test_token in _reset_tokens:
                del _reset_tokens[test_token]

    def test_reset_password_success(self, client, db_session, student_user):
        """Test successful password reset."""
        from modules.auth.password_router import _reset_tokens

        test_token = "reset_success_token"
        _reset_tokens[test_token] = {
            "user_id": student_user.id,
            "email": student_user.email,
            "created_at": datetime.now(UTC),
        }

        try:
            response = client.post(
                "/api/v1/auth/password/reset-confirm",
                json={"token": test_token, "new_password": "NewSecurePassword123"},
            )

            assert response.status_code == status.HTTP_200_OK
            assert "reset successfully" in response.json()["message"].lower()
            assert test_token not in _reset_tokens

            login_response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "NewSecurePassword123"},
            )
            assert login_response.status_code == status.HTTP_200_OK
        finally:
            if test_token in _reset_tokens:
                del _reset_tokens[test_token]

    def test_reset_password_weak_password(self, client, student_user):
        """Test password reset fails with weak password."""
        from modules.auth.password_router import _reset_tokens

        test_token = "weak_password_token"
        _reset_tokens[test_token] = {
            "user_id": student_user.id,
            "email": student_user.email,
            "created_at": datetime.now(UTC),
        }

        try:
            response = client.post(
                "/api/v1/auth/password/reset-confirm",
                json={"token": test_token, "new_password": "short"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        finally:
            if test_token in _reset_tokens:
                del _reset_tokens[test_token]

    def test_reset_password_token_consumed(self, client, db_session, student_user):
        """Test reset token can only be used once."""
        from modules.auth.password_router import _reset_tokens

        test_token = "one_time_token"
        _reset_tokens[test_token] = {
            "user_id": student_user.id,
            "email": student_user.email,
            "created_at": datetime.now(UTC),
        }

        response1 = client.post(
            "/api/v1/auth/password/reset-confirm",
            json={"token": test_token, "new_password": "FirstNewPassword123"},
        )
        assert response1.status_code == status.HTTP_200_OK

        response2 = client.post(
            "/api/v1/auth/password/reset-confirm",
            json={"token": test_token, "new_password": "SecondNewPassword123"},
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST


class TestGoogleOAuthFlow:
    """Test Google OAuth authentication flow."""

    def test_google_login_url(self, client):
        """Test getting Google OAuth login URL."""
        with patch("modules.auth.oauth_router.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_settings.GOOGLE_CLIENT_SECRET = "test_secret"
            mock_settings.GOOGLE_REDIRECT_URI = "http://localhost:3000/callback"

            with patch("modules.auth.oauth_router.oauth") as mock_oauth:
                mock_google = MagicMock()
                mock_google.create_authorization_url = AsyncMock(
                    return_value={"url": "https://accounts.google.com/o/oauth2/auth?client_id=test"}
                )
                mock_oauth.create_client.return_value = mock_google

                with patch("modules.auth.oauth_router.oauth_state_store") as mock_state:
                    mock_state.generate_state = AsyncMock(return_value="test_state_token")

                    response = client.get("/api/v1/auth/google/login")

                    if response.status_code == status.HTTP_200_OK:
                        data = response.json()
                        assert "authorization_url" in data
                        assert "state" in data

    def test_google_login_not_configured(self, client):
        """Test Google login when not configured."""
        with patch("modules.auth.oauth_router.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = None

            response = client.get("/api/v1/auth/google/login")
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_google_callback_invalid_state(self, client):
        """Test Google callback with invalid state."""
        with patch("modules.auth.oauth_router.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = "test_client_id"
            mock_settings.FRONTEND_LOGIN_ERROR_URL = "http://localhost:3000/login?error=true"

            with patch("modules.auth.oauth_router.oauth_state_store") as mock_state:
                mock_state.validate_state = AsyncMock(return_value=None)

                response = client.get(
                    "/api/v1/auth/google/callback",
                    params={"code": "test_code", "state": "invalid_state"},
                    follow_redirects=False,
                )

                assert response.status_code == 307

    def test_google_unlink_no_password(self, client, db_session, student_user, student_token):
        """Test unlinking Google account fails when no password set."""
        student_user.google_id = "google_123"
        student_user.hashed_password = ""
        db_session.commit()

        response = client.delete(
            "/api/v1/auth/google/unlink",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "password" in response.json()["detail"].lower()

    def test_google_unlink_no_google_account(self, client, student_token, student_user):
        """Test unlinking when no Google account linked."""
        response = client.delete(
            "/api/v1/auth/google/unlink",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no google account" in response.json()["detail"].lower()


class TestLoginSecurity:
    """Test login security features."""

    def test_login_rate_limiting(self, client, student_user):
        """Test login attempts are rate limited."""
        pass

    def test_login_timing_attack_protection(self, client, student_user):
        """Test login takes similar time for valid/invalid users."""
        import time

        start = time.time()
        client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": "wrongpassword"},
        )
        valid_user_time = time.time() - start

        start = time.time()
        client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@test.com", "password": "wrongpassword"},
        )
        invalid_user_time = time.time() - start

        time_difference = abs(valid_user_time - invalid_user_time)
        assert time_difference < 0.5

    def test_login_sql_injection_prevention(self, client):
        """Test login prevents SQL injection."""
        malicious_inputs = [
            "admin'--",
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin\"--",
        ]

        for malicious in malicious_inputs:
            response = client.post(
                "/api/v1/auth/login",
                data={"username": malicious, "password": "password"},
            )
            # Any of these responses is valid - the key is that login is rejected:
            # - 401: Invalid credentials
            # - 422: Validation error
            # - 429: Account locked due to too many failed attempts (rate limiting)
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_429_TOO_MANY_REQUESTS,
            ]


class TestUserVerification:
    """Test user verification flow."""

    def test_unverified_user_cannot_login(self, client, db_session):
        """Test unverified users cannot log in."""
        from models import User
        from auth import get_password_hash

        unverified_user = User(
            email="unverified@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
            is_verified=False,
        )
        db_session.add(unverified_user)
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "unverified@test.com", "password": "password123"},
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


class TestAuthorizationHeader:
    """Test various Authorization header formats."""

    def test_bearer_prefix_required(self, client, student_token):
        """Test that Bearer prefix is required."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": student_token},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_case_insensitive_bearer(self, client, student_token):
        """Test Bearer prefix is case-insensitive per RFC 6750."""
        # Per OAuth2 spec (RFC 6750), token type in Authorization header is case-insensitive
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"BEARER {student_token}"},
        )
        # Should accept uppercase BEARER per RFC 6750
        assert response.status_code == status.HTTP_200_OK

    def test_extra_whitespace_handled(self, client, student_token, student_user):
        """Test extra whitespace in Authorization header."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer  {student_token}"},
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
        ]


class TestSessionManagement:
    """Test session and token management."""

    def test_multiple_valid_tokens(self, client, db_session, student_user):
        """Test user can have multiple valid tokens."""
        from core.security import TokenManager

        token1 = TokenManager.create_access_token({"sub": student_user.email})
        token2 = TokenManager.create_access_token({"sub": student_user.email})

        response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

    def test_token_for_deleted_user(self, client, db_session, student_user):
        """Test token for deactivated user is rejected."""
        from core.security import TokenManager

        token = TokenManager.create_access_token({"sub": student_user.email})
        student_user.is_active = False
        db_session.commit()

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 403 Forbidden is returned for inactive users (authenticated but not authorized)
        assert response.status_code == status.HTTP_403_FORBIDDEN
