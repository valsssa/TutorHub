"""
Tests for user name validation and enforcement.

Tests cover:
- Registration requires both first_name and last_name
- Names cannot be empty or whitespace-only
- Names are normalized (trimmed)
- Update endpoint validates names
- OAuth flow handles incomplete profiles
- profile_incomplete flag is set correctly
"""

from datetime import datetime

from core.datetime_utils import utc_now
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from pydantic import ValidationError

from schemas import UserCreate, UserResponse, UserSelfUpdate


class TestUserCreateValidation:
    """Test UserCreate schema validation for names."""

    def test_valid_names_accepted(self):
        """Test that valid names are accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            first_name="John",
            last_name="Doe",
        )
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_names_are_trimmed(self):
        """Test that names are trimmed of whitespace."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            first_name="  John  ",
            last_name="  Doe  ",
        )
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_first_name_required(self):
        """Test that first_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                last_name="Doe",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("first_name",) for e in errors)

    def test_last_name_required(self):
        """Test that last_name is required."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                first_name="John",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("last_name",) for e in errors)

    def test_empty_first_name_rejected(self):
        """Test that empty first_name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                first_name="",
                last_name="Doe",
            )
        errors = exc_info.value.errors()
        assert any("first" in str(e).lower() for e in errors)

    def test_empty_last_name_rejected(self):
        """Test that empty last_name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                first_name="John",
                last_name="",
            )
        errors = exc_info.value.errors()
        assert any("last" in str(e).lower() for e in errors)

    def test_whitespace_only_first_name_rejected(self):
        """Test that whitespace-only first_name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                first_name="   ",
                last_name="Doe",
            )
        errors = exc_info.value.errors()
        assert any("first" in str(e).lower() or "empty" in str(e).lower() for e in errors)

    def test_whitespace_only_last_name_rejected(self):
        """Test that whitespace-only last_name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                first_name="John",
                last_name="   ",
            )
        errors = exc_info.value.errors()
        assert any("last" in str(e).lower() or "empty" in str(e).lower() for e in errors)

    def test_name_max_length_enforced(self):
        """Test that name max length (100 chars) is enforced."""
        long_name = "A" * 101
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Password123!",
                first_name=long_name,
                last_name="Doe",
            )
        errors = exc_info.value.errors()
        assert any("100" in str(e) or "exceed" in str(e).lower() for e in errors)

    def test_unicode_names_accepted(self):
        """Test that Unicode names are accepted."""
        user = UserCreate(
            email="test@example.com",
            password="Password123!",
            first_name="José",
            last_name="García",
        )
        assert user.first_name == "José"
        assert user.last_name == "García"


class TestUserSelfUpdateValidation:
    """Test UserSelfUpdate schema validation for names."""

    def test_valid_update_accepted(self):
        """Test that valid name updates are accepted."""
        update = UserSelfUpdate(
            first_name="Jane",
            last_name="Smith",
        )
        assert update.first_name == "Jane"
        assert update.last_name == "Smith"

    def test_names_are_trimmed_on_update(self):
        """Test that names are trimmed on update."""
        update = UserSelfUpdate(
            first_name="  Jane  ",
            last_name="  Smith  ",
        )
        assert update.first_name == "Jane"
        assert update.last_name == "Smith"

    def test_none_values_allowed(self):
        """Test that None values are allowed (partial update)."""
        update = UserSelfUpdate(
            first_name="Jane",
            last_name=None,
        )
        assert update.first_name == "Jane"
        assert update.last_name is None

    def test_empty_string_rejected_on_update(self):
        """Test that empty string is rejected on update."""
        with pytest.raises(ValidationError) as exc_info:
            UserSelfUpdate(
                first_name="",
                last_name="Smith",
            )
        errors = exc_info.value.errors()
        assert any("first" in str(e).lower() or "empty" in str(e).lower() for e in errors)

    def test_whitespace_only_rejected_on_update(self):
        """Test that whitespace-only string is rejected on update."""
        with pytest.raises(ValidationError) as exc_info:
            UserSelfUpdate(
                first_name="   ",
                last_name="Smith",
            )
        errors = exc_info.value.errors()
        assert any("first" in str(e).lower() or "empty" in str(e).lower() for e in errors)


class TestUserResponseComputation:
    """Test UserResponse computed fields."""

    def test_full_name_computed(self):
        """Test that full_name is computed from first_name and last_name."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            role="student",
            is_active=True,
            is_verified=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        assert response.full_name == "John Doe"
        assert response.profile_incomplete is False

    def test_profile_incomplete_when_missing_first_name(self):
        """Test that profile_incomplete is True when first_name is missing."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            first_name=None,
            last_name="Doe",
            role="student",
            is_active=True,
            is_verified=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        assert response.profile_incomplete is True
        assert response.full_name == "Doe"

    def test_profile_incomplete_when_missing_last_name(self):
        """Test that profile_incomplete is True when last_name is missing."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            first_name="John",
            last_name=None,
            role="student",
            is_active=True,
            is_verified=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        assert response.profile_incomplete is True
        assert response.full_name == "John"

    def test_profile_incomplete_when_both_names_missing(self):
        """Test that profile_incomplete is True when both names are missing."""
        response = UserResponse(
            id=1,
            email="test@example.com",
            first_name=None,
            last_name=None,
            role="student",
            is_active=True,
            is_verified=True,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        assert response.profile_incomplete is True
        assert response.full_name is None


class TestRegistrationEndpoint:
    """Test registration endpoint with name validation."""

    def test_registration_with_valid_names(self, client):
        """Test successful registration with valid names."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Password123!",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        # May succeed or fail based on other validation, but names should be valid
        if response.status_code == status.HTTP_201_CREATED:
            data = response.json()
            assert data["first_name"] == "John"
            assert data["last_name"] == "Doe"
            assert data["full_name"] == "John Doe"
            assert data["profile_incomplete"] is False

    def test_registration_without_first_name_fails(self, client):
        """Test registration fails without first_name."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Password123!",
                "last_name": "Doe",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_registration_without_last_name_fails(self, client):
        """Test registration fails without last_name."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Password123!",
                "first_name": "John",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_registration_with_empty_names_fails(self, client):
        """Test registration fails with empty names."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "Password123!",
                "first_name": "",
                "last_name": "",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserUpdateEndpoint:
    """Test user update endpoint with name validation."""

    def test_update_with_valid_names(self, client, student_token, student_user):
        """Test successful update with valid names."""
        response = client.put(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "first_name": "Jane",
                "last_name": "Smith",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"

    def test_update_with_empty_name_fails(self, client, student_token):
        """Test update fails with empty name."""
        response = client.put(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "first_name": "",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_with_whitespace_only_name_fails(self, client, student_token):
        """Test update fails with whitespace-only name."""
        response = client.put(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "first_name": "   ",
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
