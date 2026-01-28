"""Tests for security utilities (password hashing and JWT)."""

from datetime import timedelta

import pytest

from core.exceptions import AuthenticationError
from core.security import PasswordHasher, TokenManager


class TestPasswordHasher:
    """Test PasswordHasher class."""

    def test_hash_creates_bcrypt_hash(self):
        """Test that hash creates bcrypt format."""
        password = "TestPassword123!"
        hashed = PasswordHasher.hash(password)

        # Bcrypt hashes start with $2a$, $2b$, or $2y$
        assert hashed.startswith("$2")
        assert len(hashed) == 60  # Standard bcrypt hash length

    def test_hash_uses_12_rounds(self):
        """Test that hash uses 12 rounds (cost factor)."""
        password = "TestPassword123!"
        hashed = PasswordHasher.hash(password)

        # The cost factor is in the second field: $2b$12$...
        parts = hashed.split("$")
        assert parts[2] == "12"

    def test_hash_different_each_time(self):
        """Test that hashing same password produces different hashes (salt)."""
        password = "TestPassword123!"
        hash1 = PasswordHasher.hash(password)
        hash2 = PasswordHasher.hash(password)

        assert hash1 != hash2

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test verifying wrong password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify(wrong_password, hashed) is False

    def test_verify_empty_password(self):
        """Test verifying empty password."""
        password = "TestPassword123!"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify("", hashed) is False

    def test_verify_invalid_hash(self):
        """Test verifying with invalid hash format."""
        result = PasswordHasher.verify("password", "not-a-valid-hash")
        assert result is False

    def test_hash_unicode_password(self):
        """Test hashing Unicode password."""
        password = "密码Password123!"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify(password, hashed) is True

    def test_hash_long_password_truncation(self):
        """Test that passwords over 72 bytes are handled."""
        # Bcrypt has a 72-byte limit
        long_password = "a" * 100
        hashed = PasswordHasher.hash(long_password)

        # The first 72 characters should verify
        assert PasswordHasher.verify(long_password[:72], hashed) is True

    def test_hash_special_characters(self):
        """Test hashing passwords with special characters."""
        passwords = [
            "P@$$w0rd!",
            "Test123!@#$%^&*()",
            "pass\nword",  # Newline
            "pass\tword",  # Tab
            "pass word",  # Space
        ]

        for password in passwords:
            hashed = PasswordHasher.hash(password)
            assert PasswordHasher.verify(password, hashed) is True

    def test_verify_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "TestPassword123!"
        hashed = PasswordHasher.hash(password)

        assert PasswordHasher.verify("testpassword123!", hashed) is False
        assert PasswordHasher.verify("TESTPASSWORD123!", hashed) is False


class TestTokenManager:
    """Test TokenManager class."""

    def test_create_access_token_basic(self):
        """Test creating basic access token."""
        data = {"sub": "user@example.com"}
        token = TokenManager.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test creating token with custom expiry."""
        data = {"sub": "user@example.com"}
        expires = timedelta(hours=1)
        token = TokenManager.create_access_token(data, expires_delta=expires)

        assert token is not None
        # Should be able to decode
        payload = TokenManager.decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert "exp" in payload

    def test_decode_valid_token(self):
        """Test decoding valid token."""
        original_data = {"sub": "user@example.com", "role": "student"}
        token = TokenManager.create_access_token(original_data)

        payload = TokenManager.decode_token(token)
        assert payload["sub"] == "user@example.com"
        assert payload["role"] == "student"

    def test_decode_invalid_token_raises(self):
        """Test decoding invalid token raises error."""
        with pytest.raises(AuthenticationError) as exc_info:
            TokenManager.decode_token("invalid.token.here")

        assert "invalid token" in str(exc_info.value).lower()

    def test_decode_tampered_token_raises(self):
        """Test decoding tampered token raises error."""
        token = TokenManager.create_access_token({"sub": "user@example.com"})

        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1][:-5] + "xxxxx"  # Modify payload
        tampered = ".".join(parts)

        with pytest.raises(AuthenticationError):
            TokenManager.decode_token(tampered)

    def test_token_contains_expiry(self):
        """Test that token contains expiration claim."""
        data = {"sub": "user@example.com"}
        token = TokenManager.create_access_token(data)
        payload = TokenManager.decode_token(token)

        assert "exp" in payload

    def test_create_token_preserves_all_data(self):
        """Test that all data is preserved in token."""
        data = {
            "sub": "user@example.com",
            "role": "admin",
            "user_id": 123,
            "custom_field": "value",
        }
        token = TokenManager.create_access_token(data)
        payload = TokenManager.decode_token(token)

        assert payload["sub"] == data["sub"]
        assert payload["role"] == data["role"]
        assert payload["user_id"] == data["user_id"]
        assert payload["custom_field"] == data["custom_field"]

    def test_different_tokens_for_different_users(self):
        """Test that different users get different tokens."""
        token1 = TokenManager.create_access_token({"sub": "user1@example.com"})
        token2 = TokenManager.create_access_token({"sub": "user2@example.com"})

        assert token1 != token2

    def test_decode_empty_string_raises(self):
        """Test decoding empty string raises error."""
        with pytest.raises(AuthenticationError):
            TokenManager.decode_token("")

    def test_decode_malformed_token_raises(self):
        """Test decoding malformed token raises error."""
        malformed_tokens = [
            "notajwt",
            "only.twoparts",
            "way.too.many.parts.here",
            ".empty.start",
            "empty.end.",
        ]

        for malformed in malformed_tokens:
            with pytest.raises(AuthenticationError):
                TokenManager.decode_token(malformed)


class TestPasswordHasherEdgeCases:
    """Test edge cases for password hashing."""

    def test_very_short_password(self):
        """Test hashing very short password."""
        password = "a"
        hashed = PasswordHasher.hash(password)
        assert PasswordHasher.verify(password, hashed) is True

    def test_only_numbers(self):
        """Test hashing password with only numbers."""
        password = "12345678"
        hashed = PasswordHasher.hash(password)
        assert PasswordHasher.verify(password, hashed) is True

    def test_only_special_chars(self):
        """Test hashing password with only special characters."""
        password = "!@#$%^&*()"
        hashed = PasswordHasher.hash(password)
        assert PasswordHasher.verify(password, hashed) is True

    def test_unicode_characters(self):
        """Test hashing with various Unicode characters."""
        passwords = [
            "パスワード123",  # Japanese
            "пароль123",  # Russian
            "كلمةالسر",  # Arabic
            "🔐🔑🔒",  # Emojis
        ]

        for password in passwords:
            hashed = PasswordHasher.hash(password)
            assert PasswordHasher.verify(password, hashed) is True


class TestTokenManagerEdgeCases:
    """Test edge cases for token management."""

    def test_token_with_nested_data(self):
        """Test token with nested data structures."""
        data = {
            "sub": "user@example.com",
            "permissions": ["read", "write"],
            "metadata": {"key": "value"},
        }
        token = TokenManager.create_access_token(data)
        payload = TokenManager.decode_token(token)

        assert payload["permissions"] == ["read", "write"]
        assert payload["metadata"] == {"key": "value"}

    def test_token_with_numeric_values(self):
        """Test token with numeric values."""
        data = {
            "sub": "user@example.com",
            "user_id": 123,
            "balance": 99.99,
        }
        token = TokenManager.create_access_token(data)
        payload = TokenManager.decode_token(token)

        assert payload["user_id"] == 123
        assert payload["balance"] == 99.99

    def test_token_with_boolean_values(self):
        """Test token with boolean values."""
        data = {
            "sub": "user@example.com",
            "is_admin": True,
            "is_verified": False,
        }
        token = TokenManager.create_access_token(data)
        payload = TokenManager.decode_token(token)

        assert payload["is_admin"] is True
        assert payload["is_verified"] is False

    def test_token_with_none_values(self):
        """Test token with None values."""
        data = {
            "sub": "user@example.com",
            "optional_field": None,
        }
        token = TokenManager.create_access_token(data)
        payload = TokenManager.decode_token(token)

        assert payload["optional_field"] is None

    def test_very_short_expiry(self):
        """Test token with very short expiry."""
        data = {"sub": "user@example.com"}
        expires = timedelta(seconds=1)
        token = TokenManager.create_access_token(data, expires_delta=expires)

        # Should be valid immediately
        payload = TokenManager.decode_token(token)
        assert payload["sub"] == "user@example.com"

    def test_very_long_expiry(self):
        """Test token with very long expiry."""
        data = {"sub": "user@example.com"}
        expires = timedelta(days=365)
        token = TokenManager.create_access_token(data, expires_delta=expires)

        payload = TokenManager.decode_token(token)
        assert payload["sub"] == "user@example.com"
