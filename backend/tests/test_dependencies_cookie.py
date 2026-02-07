"""Tests for cookie-based token extraction in dependencies."""

from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request

from core.dependencies import extract_token_from_request, get_current_user_from_request


@pytest.fixture
def mock_request():
    """Create mock request with configurable cookies and headers."""
    request = MagicMock(spec=Request)
    request.cookies = {}
    request.headers = {}
    return request


def test_extract_token_from_cookie(mock_request):
    """Token extracted from cookie when present."""
    mock_request.cookies = {"access_token": "cookie_token_value"}
    mock_request.headers = {}
    token = extract_token_from_request(mock_request)
    assert token == "cookie_token_value"


def test_extract_token_from_header(mock_request):
    """Token extracted from Authorization header when no cookie."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer header_token_value"}
    token = extract_token_from_request(mock_request)
    assert token == "header_token_value"


def test_cookie_takes_precedence_over_header(mock_request):
    """Cookie token preferred over header for gradual migration."""
    mock_request.cookies = {"access_token": "cookie_token"}
    mock_request.headers = {"authorization": "Bearer header_token"}
    token = extract_token_from_request(mock_request)
    assert token == "cookie_token"


def test_extract_token_returns_none_when_missing(mock_request):
    """None returned when no token found anywhere."""
    mock_request.cookies = {}
    mock_request.headers = {}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_malformed_header(mock_request):
    """Malformed Authorization header returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "InvalidFormat"}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_empty_bearer(mock_request):
    """Empty Bearer token returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer "}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_bearer_only(mock_request):
    """'Bearer' without space or token returns None."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer"}
    token = extract_token_from_request(mock_request)
    assert token is None


def test_extract_token_handles_case_insensitive_header(mock_request):
    """Authorization header lookup should work with lowercase."""
    mock_request.cookies = {}
    mock_request.headers = {"authorization": "Bearer case_insensitive_token"}
    token = extract_token_from_request(mock_request)
    assert token == "case_insensitive_token"


def test_extract_token_handles_empty_cookie(mock_request):
    """Empty cookie value falls back to header."""
    mock_request.cookies = {"access_token": ""}
    mock_request.headers = {"authorization": "Bearer fallback_token"}
    token = extract_token_from_request(mock_request)
    assert token == "fallback_token"


# =============================================================================
# Tests for get_current_user_from_request
# =============================================================================


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return MagicMock()


@pytest.fixture
def mock_user():
    """Create mock user."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.is_active = True
    user.role = "student"
    user.password_changed_at = None
    user.deleted_at = None
    return user


class TestGetCurrentUserFromRequest:
    """Tests for get_current_user_from_request dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_from_cookie(self, mock_request, mock_db, mock_user):
        """Token from cookie authenticates user successfully."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",
                "pwd_ts": None,
                "type": "access",
            }

            user = await get_current_user_from_request(mock_request, mock_db)

            assert user.email == "test@example.com"
            mock_tm.decode_token.assert_called_once_with("valid_token", expected_type="access")

    @pytest.mark.asyncio
    async def test_get_current_user_from_header(self, mock_request, mock_db, mock_user):
        """Token from Authorization header authenticates user successfully."""
        mock_request.cookies = {}
        mock_request.headers = {"authorization": "Bearer header_token"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",
                "pwd_ts": None,
                "type": "access",
            }

            user = await get_current_user_from_request(mock_request, mock_db)

            assert user.email == "test@example.com"
            mock_tm.decode_token.assert_called_once_with("header_token", expected_type="access")

    @pytest.mark.asyncio
    async def test_get_current_user_no_token_raises_401(self, mock_request, mock_db):
        """No token in cookie or header raises 401."""
        mock_request.cookies = {}
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_request(mock_request, mock_db)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_raises_401(self, mock_request, mock_db):
        """Invalid token raises 401."""
        from core.exceptions import AuthenticationError

        mock_request.cookies = {"access_token": "invalid_token"}
        mock_request.headers = {}

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.side_effect = AuthenticationError("Invalid token")

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found_raises_401(self, mock_request, mock_db):
        """User not found raises 401."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "unknown@example.com",
                "role": "student",
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_current_user_inactive_raises_403(self, mock_request, mock_db, mock_user):
        """Inactive user raises 403."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 403
            assert "inactive" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_password_changed_invalidates_token(self, mock_request, mock_db, mock_user):
        """Token invalidated after password change."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}
        mock_user.password_changed_at = utc_now()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",
                "pwd_ts": (utc_now() - timedelta(hours=1)).timestamp(),
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "password change" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_password_changed_no_pwd_ts_invalidates(self, mock_request, mock_db, mock_user):
        """Old token without pwd_ts invalidated after password change."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}
        mock_user.password_changed_at = utc_now()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_role_changed_invalidates_token(self, mock_request, mock_db, mock_user):
        """Token invalidated when role changes."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}
        mock_user.role = "tutor"  # Changed from student to tutor
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",  # Token still has old role
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 401
            assert "role" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_cookie_takes_precedence_over_header(self, mock_request, mock_db, mock_user):
        """Cookie token is used when both cookie and header present."""
        mock_request.cookies = {"access_token": "cookie_token"}
        mock_request.headers = {"authorization": "Bearer header_token"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "sub": "test@example.com",
                "role": "student",
            }

            user = await get_current_user_from_request(mock_request, mock_db)

            assert user.email == "test@example.com"
            # Verify cookie token was used, not header token
            mock_tm.decode_token.assert_called_once_with("cookie_token", expected_type="access")

    @pytest.mark.asyncio
    async def test_missing_sub_in_token_raises_401(self, mock_request, mock_db):
        """Token without sub claim raises 401."""
        mock_request.cookies = {"access_token": "valid_token"}
        mock_request.headers = {}

        with patch("core.dependencies.TokenManager") as mock_tm:
            mock_tm.decode_token.return_value = {
                "role": "student",
                # No "sub" claim
            }

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(mock_request, mock_db)

            assert exc_info.value.status_code == 401
