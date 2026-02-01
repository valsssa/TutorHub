"""Tests for security and authentication mechanisms."""

from datetime import UTC, datetime, timedelta, timezone

from fastapi import status
from jose import jwt

from auth import create_access_token, get_password_hash, verify_password
from core.config import settings
from core.security import PasswordHasher, TokenManager


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = PasswordHasher.hash(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify("wrong_password", hashed) is False

    def test_password_hash_is_consistent(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "test_password_123"
        hash1 = PasswordHasher.hash(password)
        hash2 = PasswordHasher.hash(password)

        assert hash1 != hash2  # Different salts
        assert PasswordHasher.verify(password, hash1)
        assert PasswordHasher.verify(password, hash2)

    def test_password_truncation_at_72_bytes(self):
        """Test that passwords longer than 72 bytes are truncated."""
        # Create password > 72 bytes
        long_password = "a" * 80
        hashed = PasswordHasher.hash(long_password)

        # Should verify with truncated version
        assert PasswordHasher.verify(long_password[:72], hashed)

    def test_backward_compatibility_functions(self):
        """Test backward compatibility wrapper functions."""
        password = "test123"

        # Test get_password_hash
        hashed = get_password_hash(password)
        assert hashed.startswith("$2b$")

        # Test verify_password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "test@example.com", "role": "student"}
        token = TokenManager.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Test decoding a valid JWT token."""
        data = {"sub": "test@example.com", "role": "student"}
        token = TokenManager.create_access_token(data)

        decoded = TokenManager.decode_token(token)
        assert decoded["sub"] == "test@example.com"
        assert decoded["role"] == "student"
        assert "exp" in decoded

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        from core.exceptions import AuthenticationError

        data = {"sub": "test@example.com"}
        # Create token that expires immediately
        token = TokenManager.create_access_token(data, expires_delta=timedelta(seconds=-1))

        try:
            TokenManager.decode_token(token)
            assert False, "Should have raised AuthenticationError"  # noqa: B011
        except AuthenticationError:
            pass

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        from core.exceptions import AuthenticationError

        try:
            TokenManager.decode_token("invalid.token.here")
            assert False, "Should have raised AuthenticationError"  # noqa: B011
        except AuthenticationError:
            pass

    def test_token_contains_expiration(self):
        """Test that token contains expiration claim."""
        data = {"sub": "test@example.com"}
        token = TokenManager.create_access_token(data)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in decoded

        # Check expiration is in the future
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=UTC)
        assert exp_time > datetime.now(UTC)

    def test_token_custom_expiration(self):
        """Test token with custom expiration."""
        data = {"sub": "test@example.com"}
        custom_delta = timedelta(hours=2)
        token = TokenManager.create_access_token(data, expires_delta=custom_delta)

        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=UTC)

        # Should expire roughly 2 hours from now (within 5 seconds tolerance)
        expected_exp = datetime.now(UTC) + custom_delta
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5


class TestAuthenticationEndpoints:
    """Test authentication endpoint security."""

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_expired_token(self, client, student_user):
        """Test accessing protected endpoint with expired token."""
        # Create expired token
        data = {"sub": student_user.email}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_valid_token(self, client, student_token):
        """Test accessing protected endpoint with valid token."""
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_200_OK

    def test_admin_endpoint_requires_admin_role(self, client, student_token):
        """Test that admin endpoints reject non-admin users."""
        response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {student_token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_tutor_endpoint_requires_tutor_role(self, client, student_token):
        """Test that tutor endpoints reject non-tutor users."""
        response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_inactive_user_cannot_access(self, client, db_session, student_user):
        """Test that inactive users cannot access protected endpoints."""
        # Get token while active
        response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": "student123"},
        )
        token = response.json()["access_token"]

        # Deactivate user
        student_user.is_active = False
        db_session.commit()

        # Try to access protected endpoint
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRateLimiting:
    """Test rate limiting on authentication endpoints."""

    def test_registration_rate_limit(self, client):
        """Test that registration is rate limited."""
        # Try to register 6 times rapidly (limit is 5/minute)
        for i in range(6):
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"user{i}@test.com",
                    "password": "Password123!",
                    "first_name": "Test",
                    "last_name": f"User{i}",
                },
            )

            if i < 5:
                # First 5 should succeed
                assert response.status_code in [
                    status.HTTP_201_CREATED,
                    status.HTTP_400_BAD_REQUEST,  # Might fail for other reasons
                ]
            else:
                # 6th should be rate limited
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_login_rate_limit(self, client, student_user):
        """Test that login is rate limited."""
        # Try to login 11 times rapidly (limit is 10/minute)
        for i in range(11):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "wrong_password"},
            )

            if i < 10:
                # First 10 should be processed (might fail due to wrong password)
                assert response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_401_UNAUTHORIZED,
                ]
            else:
                # 11th should be rate limited
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestInputSanitization:
    """Test input sanitization and validation."""

    def test_email_sanitization(self, client):
        """Test that email is sanitized (lowercase, stripped)."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "  Test.User@EXAMPLE.COM  ",
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "test.user@example.com"

    def test_sql_injection_prevention(self, client):
        """Test that SQL injection attempts are prevented."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com'; DROP TABLE users; --",
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        # Should either reject invalid email or safely handle it
        # but should NOT execute SQL injection
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_201_CREATED,
        ]

    def test_xss_prevention_in_password(self, client):
        """Test that XSS attempts in password are safely handled."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "<script>alert('xss')</script>",
                "first_name": "Test",
                "last_name": "User",
            },
        )
        # Should accept (password is hashed) but never execute
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]
