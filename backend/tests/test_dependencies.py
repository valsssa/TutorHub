"""Tests for FastAPI dependencies."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from core.config import Roles
from core.dependencies import (
    get_current_active_user,
    get_current_admin_user,
    get_current_owner_user,
    get_current_student_user,
    get_current_tutor_profile,
    get_current_tutor_user,
    get_current_user,
    get_current_user_optional,
)


def create_mock_request(token: str | None = None, use_header: bool = False) -> MagicMock:
    """Create a mock Request object with token in cookie or header."""
    request = MagicMock()
    if token and not use_header:
        request.cookies = {"access_token": token}
        request.headers = {}
    elif token and use_header:
        request.cookies = {}
        request.headers = {"authorization": f"Bearer {token}"}
    else:
        request.cookies = {}
        request.headers = {}
    return request


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.role = "student"
        user.is_active = True
        user.deleted_at = None
        user.password_changed_at = None
        return user

    @pytest.mark.asyncio
    async def test_valid_token(self, mock_db, mock_user):
        """Test authentication with valid token."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("valid_token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            result = await get_current_user(mock_request, mock_db)

            assert result == mock_user

    @pytest.mark.asyncio
    async def test_invalid_token(self, mock_db):
        """Test authentication with invalid token."""
        from core.exceptions import AuthenticationError

        mock_request = create_mock_request("invalid_token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.side_effect = AuthenticationError("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_email_in_token(self, mock_db):
        """Test authentication with missing email in token."""
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": None}

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_db):
        """Test authentication when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "unknown@example.com"}

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_inactive_user(self, mock_db, mock_user):
        """Test authentication for inactive user."""
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "test@example.com", "role": "student"}

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 403
            assert "inactive" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_password_changed_invalidates_token(self, mock_db, mock_user):
        """Test token invalidated after password change."""
        mock_user.password_changed_at = datetime.now(timezone.utc)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
                "pwd_ts": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp(),
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "password change" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_password_changed_without_pwd_ts(self, mock_db, mock_user):
        """Test old token without pwd_ts is invalidated after password change."""
        mock_user.password_changed_at = datetime.now(timezone.utc)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_role_changed_invalidates_token(self, mock_db, mock_user):
        """Test token invalidated when role changes."""
        mock_user.role = "tutor"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "role" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_token_provided(self, mock_db):
        """Test authentication fails when no token is provided."""
        mock_request = create_mock_request(None)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, mock_db)

        assert exc_info.value.status_code == 401
        assert "not authenticated" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_token_from_authorization_header(self, mock_db, mock_user):
        """Test authentication with token in Authorization header (legacy support)."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("header_token", use_header=True)

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            result = await get_current_user(mock_request, mock_db)

            assert result == mock_user


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional dependency."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.role = "student"
        user.is_active = True
        user.deleted_at = None
        user.password_changed_at = None
        return user

    @pytest.mark.asyncio
    async def test_no_token(self, mock_db):
        """Test returns None when no token provided."""
        mock_request = create_mock_request(None)
        result = await get_current_user_optional(mock_request, mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_token(self, mock_db):
        """Test returns None for empty token."""
        mock_request = create_mock_request(None)  # Empty cookies/headers
        result = await get_current_user_optional(mock_request, mock_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_token(self, mock_db, mock_user):
        """Test returns user for valid token."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("valid_token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            result = await get_current_user_optional(mock_request, mock_db)

            assert result == mock_user

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, mock_db):
        """Test returns None for invalid token."""
        from core.exceptions import AuthenticationError

        mock_request = create_mock_request("invalid")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.side_effect = AuthenticationError("Invalid")

            result = await get_current_user_optional(mock_request, mock_db)

            assert result is None

    @pytest.mark.asyncio
    async def test_user_not_found_returns_none(self, mock_db):
        """Test returns None when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "unknown@example.com"}

            result = await get_current_user_optional(mock_request, mock_db)

            assert result is None

    @pytest.mark.asyncio
    async def test_inactive_user_returns_none(self, mock_db, mock_user):
        """Test returns None for inactive user."""
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "test@example.com"}

            result = await get_current_user_optional(mock_request, mock_db)

            assert result is None

    @pytest.mark.asyncio
    async def test_stale_password_token_returns_none(self, mock_db, mock_user):
        """Test returns None for stale password token."""
        mock_user.password_changed_at = datetime.now(timezone.utc)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "pwd_ts": (datetime.now(timezone.utc) - timedelta(hours=1)).timestamp(),
            }

            result = await get_current_user_optional(mock_request, mock_db)

            assert result is None

    @pytest.mark.asyncio
    async def test_stale_role_token_returns_none(self, mock_db, mock_user):
        """Test returns None for stale role token."""
        mock_user.role = "tutor"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_request = create_mock_request("token")

        with patch("core.dependencies.TokenManager.decode_token") as mock_decode:
            mock_decode.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            result = await get_current_user_optional(mock_request, mock_db)

            assert result is None


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_returns_user(self):
        """Test returns the current user."""
        mock_user = MagicMock()
        result = await get_current_active_user(mock_user)
        assert result == mock_user


class TestGetCurrentAdminUser:
    """Tests for get_current_admin_user dependency."""

    @pytest.mark.asyncio
    async def test_admin_allowed(self):
        """Test admin role is allowed."""
        mock_user = MagicMock()
        mock_user.role = "admin"

        with patch.object(Roles, "has_admin_access", return_value=True):
            result = await get_current_admin_user(mock_user)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_owner_allowed(self):
        """Test owner role is allowed (higher privilege)."""
        mock_user = MagicMock()
        mock_user.role = "owner"

        with patch.object(Roles, "has_admin_access", return_value=True):
            result = await get_current_admin_user(mock_user)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_student_denied(self):
        """Test student role is denied."""
        mock_user = MagicMock()
        mock_user.role = "student"

        with patch.object(Roles, "has_admin_access", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin_user(mock_user)

            assert exc_info.value.status_code == 403
            assert "admin" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_tutor_denied(self):
        """Test tutor role is denied."""
        mock_user = MagicMock()
        mock_user.role = "tutor"

        with patch.object(Roles, "has_admin_access", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_admin_user(mock_user)

            assert exc_info.value.status_code == 403


class TestGetCurrentOwnerUser:
    """Tests for get_current_owner_user dependency."""

    @pytest.mark.asyncio
    async def test_owner_allowed(self):
        """Test owner role is allowed."""
        mock_user = MagicMock()
        mock_user.role = "owner"

        with patch.object(Roles, "is_owner", return_value=True):
            result = await get_current_owner_user(mock_user)
            assert result == mock_user

    @pytest.mark.asyncio
    async def test_admin_denied(self):
        """Test admin role is denied."""
        mock_user = MagicMock()
        mock_user.role = "admin"

        with patch.object(Roles, "is_owner", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_owner_user(mock_user)

            assert exc_info.value.status_code == 403
            assert "owner" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_student_denied(self):
        """Test student role is denied."""
        mock_user = MagicMock()
        mock_user.role = "student"

        with patch.object(Roles, "is_owner", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_owner_user(mock_user)

            assert exc_info.value.status_code == 403


class TestGetCurrentTutorUser:
    """Tests for get_current_tutor_user dependency."""

    @pytest.mark.asyncio
    async def test_tutor_allowed(self):
        """Test tutor role is allowed."""
        mock_user = MagicMock()
        mock_user.role = Roles.TUTOR

        result = await get_current_tutor_user(mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_student_denied(self):
        """Test student role is denied."""
        mock_user = MagicMock()
        mock_user.role = Roles.STUDENT

        with pytest.raises(HTTPException) as exc_info:
            await get_current_tutor_user(mock_user)

        assert exc_info.value.status_code == 403
        assert "tutor" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_admin_denied(self):
        """Test admin role is denied for tutor-only endpoints."""
        mock_user = MagicMock()
        mock_user.role = "admin"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_tutor_user(mock_user)

        assert exc_info.value.status_code == 403


class TestGetCurrentStudentUser:
    """Tests for get_current_student_user dependency."""

    @pytest.mark.asyncio
    async def test_student_allowed(self):
        """Test student role is allowed."""
        mock_user = MagicMock()
        mock_user.role = Roles.STUDENT

        result = await get_current_student_user(mock_user)
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_tutor_denied(self):
        """Test tutor role is denied."""
        mock_user = MagicMock()
        mock_user.role = Roles.TUTOR

        with pytest.raises(HTTPException) as exc_info:
            await get_current_student_user(mock_user)

        assert exc_info.value.status_code == 403
        assert "student" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_admin_denied(self):
        """Test admin role is denied for student-only endpoints."""
        mock_user = MagicMock()
        mock_user.role = "admin"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_student_user(mock_user)

        assert exc_info.value.status_code == 403


class TestGetCurrentTutorProfile:
    """Tests for get_current_tutor_profile dependency."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_tutor_user(self):
        """Create mock tutor user."""
        user = MagicMock()
        user.id = 1
        user.role = Roles.TUTOR
        return user

    @pytest.mark.asyncio
    async def test_profile_found(self, mock_tutor_user, mock_db):
        """Test returns profile when found."""
        mock_profile = MagicMock()
        mock_profile.user_id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_profile

        result = await get_current_tutor_profile(mock_tutor_user, mock_db)

        assert result == mock_profile

    @pytest.mark.asyncio
    async def test_profile_not_found(self, mock_tutor_user, mock_db):
        """Test raises 404 when profile not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_current_tutor_profile(mock_tutor_user, mock_db)

        assert exc_info.value.status_code == 404
        assert "profile" in exc_info.value.detail.lower()
