"""Tests for account lockout (brute-force protection) functionality."""

import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch

from core.account_lockout import AccountLockoutService


class TestAccountLockoutService:
    """Test the AccountLockoutService directly."""

    @pytest.fixture
    def lockout_service(self):
        """Create a fresh lockout service instance."""
        return AccountLockoutService()

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        mock.get = AsyncMock(return_value=None)
        mock.incr = AsyncMock(return_value=1)
        mock.expire = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.ttl = AsyncMock(return_value=-1)
        mock.pipeline = lambda: MockPipeline(mock)
        return mock

    @pytest.mark.asyncio
    async def test_is_locked_returns_false_when_no_attempts(
        self, lockout_service, mock_redis
    ):
        """Test that is_locked returns False when there are no failed attempts."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.return_value = None
            result = await lockout_service.is_locked("test@example.com")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_locked_returns_false_under_max_attempts(
        self, lockout_service, mock_redis
    ):
        """Test that is_locked returns False when under max attempts."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.return_value = "3"  # Under default of 5
            result = await lockout_service.is_locked("test@example.com")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_locked_returns_true_at_max_attempts(
        self, lockout_service, mock_redis
    ):
        """Test that is_locked returns True when at max attempts."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.return_value = "5"  # At default max
            result = await lockout_service.is_locked("test@example.com")
            assert result is True

    @pytest.mark.asyncio
    async def test_is_locked_returns_true_over_max_attempts(
        self, lockout_service, mock_redis
    ):
        """Test that is_locked returns True when over max attempts."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.return_value = "10"  # Over default max
            result = await lockout_service.is_locked("test@example.com")
            assert result is True

    @pytest.mark.asyncio
    async def test_record_failed_attempt_increments_counter(
        self, lockout_service, mock_redis
    ):
        """Test that record_failed_attempt increments the counter."""
        mock_pipe = MockPipeline(mock_redis)
        mock_pipe._execute_results = [1, True]
        mock_redis.pipeline = lambda: mock_pipe

        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            result = await lockout_service.record_failed_attempt("test@example.com")
            assert result == 1

    @pytest.mark.asyncio
    async def test_clear_failed_attempts_deletes_key(
        self, lockout_service, mock_redis
    ):
        """Test that clear_failed_attempts deletes the Redis key."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.delete.return_value = 1
            result = await lockout_service.clear_failed_attempts("test@example.com")
            assert result is True
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_remaining_attempts_when_no_attempts(
        self, lockout_service, mock_redis
    ):
        """Test remaining attempts returns max when no attempts recorded."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.return_value = None
            result = await lockout_service.get_remaining_attempts("test@example.com")
            assert result == 5  # Default max

    @pytest.mark.asyncio
    async def test_get_remaining_attempts_calculates_correctly(
        self, lockout_service, mock_redis
    ):
        """Test remaining attempts calculation."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.return_value = "3"
            result = await lockout_service.get_remaining_attempts("test@example.com")
            assert result == 2  # 5 - 3 = 2

    @pytest.mark.asyncio
    async def test_get_lockout_ttl_returns_remaining_seconds(
        self, lockout_service, mock_redis
    ):
        """Test TTL returns remaining seconds."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.ttl.return_value = 600
            result = await lockout_service.get_lockout_ttl("test@example.com")
            assert result == 600

    @pytest.mark.asyncio
    async def test_email_normalization(self, lockout_service):
        """Test that email is normalized (lowercase, trimmed)."""
        key1 = lockout_service._get_key("Test@Example.COM")
        key2 = lockout_service._get_key("  test@example.com  ")
        key3 = lockout_service._get_key("test@example.com")

        assert key1 == key3
        assert key2 == key3

    @pytest.mark.asyncio
    async def test_redis_error_handling_is_locked(
        self, lockout_service, mock_redis
    ):
        """Test that Redis errors are handled gracefully in is_locked."""
        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            mock_redis.get.side_effect = Exception("Redis connection error")
            result = await lockout_service.is_locked("test@example.com")
            assert result is False  # Fail open

    @pytest.mark.asyncio
    async def test_redis_error_handling_record_failed(
        self, lockout_service, mock_redis
    ):
        """Test that Redis errors are handled gracefully in record_failed_attempt."""
        mock_pipe = MockPipeline(mock_redis)
        mock_pipe._execute_error = Exception("Redis connection error")
        mock_redis.pipeline = lambda: mock_pipe

        with patch.object(
            lockout_service, "_get_redis", return_value=mock_redis
        ):
            result = await lockout_service.record_failed_attempt("test@example.com")
            assert result == 0


class MockPipeline:
    """Mock Redis pipeline for testing."""

    def __init__(self, redis_mock):
        self._redis = redis_mock
        self._commands = []
        self._execute_results = [1, True]
        self._execute_error = None

    def incr(self, key):
        self._commands.append(("incr", key))
        return self

    def expire(self, key, ttl):
        self._commands.append(("expire", key, ttl))
        return self

    async def execute(self):
        if self._execute_error:
            raise self._execute_error
        return self._execute_results


class TestLoginAccountLockout:
    """Integration tests for account lockout in login endpoint."""

    @pytest.mark.asyncio
    async def test_login_blocked_when_account_locked(self, client, student_user):
        """Test that login is blocked when account is locked."""
        with patch(
            "modules.auth.presentation.api.account_lockout.is_locked",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "modules.auth.presentation.api.account_lockout.get_lockout_ttl",
            new_callable=AsyncMock,
            return_value=600,
        ):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "student123"},
            )
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert "temporarily locked" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_records_failed_attempt_on_wrong_password(
        self, client, student_user
    ):
        """Test that failed login records an attempt."""
        with patch(
            "modules.auth.presentation.api.account_lockout.is_locked",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "modules.auth.presentation.api.account_lockout.record_failed_attempt",
            new_callable=AsyncMock,
            return_value=1,
        ) as mock_record:
            response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "wrongpassword"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            mock_record.assert_called_once_with(student_user.email)

    @pytest.mark.asyncio
    async def test_login_clears_attempts_on_success(self, client, student_user):
        """Test that successful login clears failed attempts."""
        with patch(
            "modules.auth.presentation.api.account_lockout.is_locked",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "modules.auth.presentation.api.account_lockout.clear_failed_attempts",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_clear:
            response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "student123"},
            )
            assert response.status_code == status.HTTP_200_OK
            mock_clear.assert_called_once_with(student_user.email)

    @pytest.mark.asyncio
    async def test_lockout_message_shows_time_remaining(self, client, student_user):
        """Test that lockout message shows approximate time remaining."""
        with patch(
            "modules.auth.presentation.api.account_lockout.is_locked",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "modules.auth.presentation.api.account_lockout.get_lockout_ttl",
            new_callable=AsyncMock,
            return_value=120,  # 2 minutes
        ):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "student123"},
            )
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            detail = response.json()["detail"]
            assert "2 minutes" in detail

    @pytest.mark.asyncio
    async def test_lockout_singular_minute_message(self, client, student_user):
        """Test that lockout message uses singular 'minute' for 1 minute."""
        with patch(
            "modules.auth.presentation.api.account_lockout.is_locked",
            new_callable=AsyncMock,
            return_value=True,
        ), patch(
            "modules.auth.presentation.api.account_lockout.get_lockout_ttl",
            new_callable=AsyncMock,
            return_value=30,  # 30 seconds rounds up to 1 minute
        ):
            response = client.post(
                "/api/v1/auth/login",
                data={"username": student_user.email, "password": "student123"},
            )
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            detail = response.json()["detail"]
            assert "1 minute." in detail  # Singular

    @pytest.mark.asyncio
    async def test_nonexistent_user_does_not_record_attempt(self, client):
        """Test that login attempt for nonexistent user still records attempt."""
        with patch(
            "modules.auth.presentation.api.account_lockout.is_locked",
            new_callable=AsyncMock,
            return_value=False,
        ), patch(
            "modules.auth.presentation.api.account_lockout.record_failed_attempt",
            new_callable=AsyncMock,
            return_value=1,
        ) as mock_record:
            response = client.post(
                "/api/v1/auth/login",
                data={"username": "nobody@test.com", "password": "password123"},
            )
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            mock_record.assert_called_once_with("nobody@test.com")
