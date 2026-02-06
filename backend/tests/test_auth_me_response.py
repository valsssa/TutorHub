"""Tests for /auth/me endpoint response format.

This module ensures the /auth/me endpoint returns all expected fields
including computed fields like full_name and profile_incomplete.
"""

import pytest
from fastapi import status

from tests.conftest import TEST_PASSWORD, create_test_user


class TestAuthMeResponseFormat:
    """Test /auth/me endpoint returns complete user data."""

    def test_me_response_includes_required_fields(self, client, student_user, student_token):
        """Response should include all required fields."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Core identity fields
        assert "id" in data
        assert "email" in data
        assert "role" in data

        # Name fields
        assert "first_name" in data
        assert "last_name" in data
        assert "full_name" in data
        assert "profile_incomplete" in data

        # Status fields
        assert "is_active" in data
        assert "is_verified" in data

        # Preference fields
        assert "timezone" in data
        assert "currency" in data
        assert "avatar_url" in data

        # Timestamp fields
        assert "created_at" in data
        assert "updated_at" in data

    def test_me_full_name_computed_correctly(self, client, student_user, student_token):
        """full_name should be computed from first_name + last_name."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Student user fixture has first_name="Test", last_name="Student"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Student"
        assert data["full_name"] == "Test Student"
        assert data["profile_incomplete"] is False

    def test_me_profile_incomplete_when_names_missing(self, client, db_session):
        """profile_incomplete should be True when names are missing."""
        from core.security import TokenManager

        # Create user without names
        user = create_test_user(
            db_session,
            email="nonames@test.example",
            password=TEST_PASSWORD,
            role="student",
            first_name="",  # Empty string
            last_name="",
        )
        # Set names to None directly after creation
        user.first_name = None
        user.last_name = None
        db_session.commit()

        token = TokenManager.create_access_token({"sub": user.email})

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["first_name"] is None
        assert data["last_name"] is None
        assert data["full_name"] is None
        assert data["profile_incomplete"] is True

    def test_me_profile_incomplete_when_partial_names(self, client, db_session):
        """profile_incomplete should be True when only partial names are set."""
        from core.security import TokenManager

        # Create user with only first name
        user = create_test_user(
            db_session,
            email="partialnames@test.example",
            password=TEST_PASSWORD,
            role="student",
            first_name="Jane",
            last_name="",
        )
        # Set last_name to None
        user.last_name = None
        db_session.commit()

        token = TokenManager.create_access_token({"sub": user.email})

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["first_name"] == "Jane"
        assert data["last_name"] is None
        # full_name should be just the first name when last_name is missing
        assert data["full_name"] == "Jane"
        # profile is incomplete because last_name is missing
        assert data["profile_incomplete"] is True

    def test_me_response_includes_verification_status(self, client, student_user, student_token):
        """Response should include is_verified field."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "is_verified" in data
        assert isinstance(data["is_verified"], bool)
        assert data["is_verified"] is True

    def test_me_response_includes_preferences(self, client, student_user, student_token):
        """Response should include user preferences (timezone, currency)."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["timezone"] == "UTC"
        assert data["currency"] == "USD"

    def test_me_response_includes_optional_fields(self, client, student_user, student_token):
        """Response should include optional fields (preferred_language, locale)."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # These are optional, so they may be None
        assert "preferred_language" in data
        assert "locale" in data

    def test_me_response_correct_email(self, client, student_user, student_token):
        """Response email should match the authenticated user."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["email"] == student_user.email
        assert data["id"] == student_user.id

    def test_me_response_correct_role(self, client, student_user, student_token):
        """Response role should match the user's role."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["role"] == "student"


class TestAuthMeEdgeCases:
    """Test edge cases for /auth/me endpoint."""

    def test_me_without_authentication(self, client):
        """Should return 401 without authentication."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_with_invalid_token(self, client):
        """Should return 401 with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_avatar_url_is_string_or_none(self, client, student_user, student_token):
        """avatar_url should be a string or None, not a complex object."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # avatar_url should be None or a string, never a dict
        avatar_url = data.get("avatar_url")
        assert avatar_url is None or isinstance(avatar_url, str)


class TestAuthMeTutorRole:
    """Test /auth/me for tutor users."""

    def test_tutor_me_response_format(self, client, tutor_user, tutor_token):
        """Tutor /me response should have same format as student."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Same required fields
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert data["role"] == "tutor"
        assert "full_name" in data
        assert "profile_incomplete" in data

        # Should have names set
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Tutor"
        assert data["full_name"] == "Test Tutor"
        assert data["profile_incomplete"] is False


class TestAuthMeAdminRole:
    """Test /auth/me for admin users."""

    def test_admin_me_response_format(self, client, admin_user, admin_token):
        """Admin /me response should have same format as other roles."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Same required fields
        assert "id" in data
        assert "email" in data
        assert "role" in data
        assert data["role"] == "admin"
        assert "full_name" in data
        assert "profile_incomplete" in data
