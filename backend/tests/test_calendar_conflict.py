"""Tests for the calendar conflict checking service."""

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.calendar_conflict import (
    CALENDAR_CACHE_TTL,
    CalendarAPIError,
    CalendarConflictService,
    _calendar_cache,
    invalidate_calendar_cache,
)


class TestCalendarAPIError:
    """Tests for CalendarAPIError exception."""

    def test_create_error(self):
        """Test creating a CalendarAPIError."""
        error = CalendarAPIError("Test error message")
        assert str(error) == "Test error message"

    def test_error_inheritance(self):
        """Test CalendarAPIError inherits from Exception."""
        error = CalendarAPIError("Test")
        assert isinstance(error, Exception)


class TestCalendarConflictService:
    """Tests for CalendarConflictService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return CalendarConflictService(mock_db)

    @pytest.fixture
    def mock_tutor_user(self):
        """Create mock tutor user with calendar tokens."""
        user = MagicMock()
        user.id = 123
        user.google_calendar_refresh_token = "refresh_token_123"
        user.google_calendar_access_token = "access_token_123"
        user.google_calendar_token_expires = datetime.now(UTC) + timedelta(hours=1)
        return user

    def test_init(self, service, mock_db):
        """Test service initialization."""
        assert service.db is mock_db

    @pytest.mark.asyncio
    async def test_check_no_calendar_connected(self, service):
        """Test check when tutor has no calendar connected."""
        user = MagicMock()
        user.google_calendar_refresh_token = None

        has_conflict, error = await service.check_calendar_conflict(
            user,
            datetime.now(UTC),
            datetime.now(UTC) + timedelta(hours=1),
        )

        assert has_conflict is False
        assert error is None

    @pytest.mark.asyncio
    async def test_check_no_conflict(self, service, mock_tutor_user):
        """Test check when there's no calendar conflict."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        with patch.object(service, "_fetch_busy_times", return_value=[]):
            with patch.object(service, "_get_cached_busy_times", return_value=None):
                has_conflict, error = await service.check_calendar_conflict(
                    mock_tutor_user, start, end
                )

        assert has_conflict is False
        assert error is None

    @pytest.mark.asyncio
    async def test_check_with_conflict(self, service, mock_tutor_user):
        """Test check when there is a calendar conflict."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start + timedelta(minutes=30)).isoformat(),
                "end": (start + timedelta(minutes=90)).isoformat(),
            }
        ]

        with patch.object(service, "_fetch_busy_times", return_value=busy_times):
            with patch.object(service, "_get_cached_busy_times", return_value=None):
                has_conflict, error = await service.check_calendar_conflict(
                    mock_tutor_user, start, end
                )

        assert has_conflict is True
        assert "conflict" in error.lower()

    @pytest.mark.asyncio
    async def test_check_uses_cache(self, service, mock_tutor_user):
        """Test check uses cached busy times."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)
        cached_busy = []

        with patch.object(
            service, "_get_cached_busy_times", return_value=cached_busy
        ), patch.object(service, "_fetch_busy_times") as mock_fetch:
            await service.check_calendar_conflict(mock_tutor_user, start, end)
            mock_fetch.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_api_error_graceful_degradation(
        self, service, mock_tutor_user
    ):
        """Test graceful degradation on API error."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        with patch.object(
            service,
            "_fetch_busy_times",
            side_effect=CalendarAPIError("API failed"),
        ), patch.object(service, "_get_cached_busy_times", return_value=None):
            has_conflict, error = await service.check_calendar_conflict(
                mock_tutor_user, start, end
            )

        assert has_conflict is False
        assert error is None

    @pytest.mark.asyncio
    async def test_check_adds_timezone_to_naive_datetimes(
        self, service, mock_tutor_user
    ):
        """Test that naive datetimes get UTC timezone."""
        start = datetime.utcnow()
        end = start + timedelta(hours=1)

        with patch.object(service, "_fetch_busy_times", return_value=[]):
            with patch.object(service, "_get_cached_busy_times", return_value=None):
                await service.check_calendar_conflict(mock_tutor_user, start, end)


class TestTokenExpiry:
    """Tests for token expiry handling."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return CalendarConflictService(mock_db)

    def test_token_not_expired(self, service):
        """Test token is not expired."""
        user = MagicMock()
        user.google_calendar_token_expires = datetime.now(UTC) + timedelta(hours=1)

        assert service._is_token_expired(user) is False

    def test_token_expired(self, service):
        """Test token is expired."""
        user = MagicMock()
        user.google_calendar_token_expires = datetime.now(UTC) - timedelta(minutes=1)

        assert service._is_token_expired(user) is True

    def test_token_near_expiry(self, service):
        """Test token is considered expired within 5 minute buffer."""
        user = MagicMock()
        user.google_calendar_token_expires = datetime.now(UTC) + timedelta(minutes=3)

        assert service._is_token_expired(user) is True

    def test_token_no_expiry_set(self, service):
        """Test token with no expiry is considered expired."""
        user = MagicMock()
        user.google_calendar_token_expires = None

        assert service._is_token_expired(user) is True


class TestOverlapDetection:
    """Tests for time overlap detection."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return CalendarConflictService(mock_db)

    def test_no_overlap_before(self, service):
        """Test no overlap when busy time is before booking."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start - timedelta(hours=2)).isoformat(),
                "end": (start - timedelta(hours=1)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is False

    def test_no_overlap_after(self, service):
        """Test no overlap when busy time is after booking."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (end + timedelta(hours=1)).isoformat(),
                "end": (end + timedelta(hours=2)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is False

    def test_overlap_partial_start(self, service):
        """Test overlap when busy time overlaps start."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start - timedelta(minutes=30)).isoformat(),
                "end": (start + timedelta(minutes=30)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is True

    def test_overlap_partial_end(self, service):
        """Test overlap when busy time overlaps end."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (end - timedelta(minutes=30)).isoformat(),
                "end": (end + timedelta(minutes=30)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is True

    def test_overlap_contained(self, service):
        """Test overlap when booking is contained in busy time."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start - timedelta(hours=1)).isoformat(),
                "end": (end + timedelta(hours=1)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is True

    def test_overlap_contains(self, service):
        """Test overlap when busy time is contained in booking."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start + timedelta(minutes=15)).isoformat(),
                "end": (start + timedelta(minutes=45)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is True

    def test_no_overlap_adjacent_before(self, service):
        """Test no overlap when busy ends exactly at booking start."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start - timedelta(hours=1)).isoformat(),
                "end": start.isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is False

    def test_no_overlap_adjacent_after(self, service):
        """Test no overlap when busy starts exactly at booking end."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": end.isoformat(),
                "end": (end + timedelta(hours=1)).isoformat(),
            }
        ]

        assert service._check_overlap(busy_times, start, end) is False

    def test_malformed_busy_times(self, service):
        """Test handling of malformed busy times."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {"start": "invalid", "end": "invalid"},
            {"start": "", "end": ""},
            {},
        ]

        assert service._check_overlap(busy_times, start, end) is False

    def test_multiple_busy_times_one_overlaps(self, service):
        """Test with multiple busy times where one overlaps."""
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        busy_times = [
            {
                "start": (start - timedelta(hours=3)).isoformat(),
                "end": (start - timedelta(hours=2)).isoformat(),
            },
            {
                "start": (start + timedelta(minutes=30)).isoformat(),
                "end": (start + timedelta(minutes=90)).isoformat(),
            },
            {
                "start": (end + timedelta(hours=1)).isoformat(),
                "end": (end + timedelta(hours=2)).isoformat(),
            },
        ]

        assert service._check_overlap(busy_times, start, end) is True


class TestCaching:
    """Tests for calendar cache functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return CalendarConflictService(mock_db)

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        _calendar_cache.clear()
        yield
        _calendar_cache.clear()

    def test_get_cache_key(self, service):
        """Test cache key generation."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        end = datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)

        key = service._get_cache_key(123, start, end)

        assert "calendar_busy:123:" in key
        assert "2024-01-15" in key

    def test_get_cache_key_rounds_to_minute(self, service):
        """Test cache key rounds times to minute precision."""
        start1 = datetime(2024, 1, 15, 10, 0, 30, 123456, tzinfo=UTC)
        start2 = datetime(2024, 1, 15, 10, 0, 45, 654321, tzinfo=UTC)
        end = datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)

        key1 = service._get_cache_key(123, start1, end)
        key2 = service._get_cache_key(123, start2, end)

        assert key1 == key2

    def test_cache_busy_times(self, service):
        """Test caching busy times."""
        busy_times = [{"start": "2024-01-15T10:00:00", "end": "2024-01-15T11:00:00"}]
        cache_key = "calendar_busy:123:test"

        service._cache_busy_times(cache_key, busy_times)

        assert cache_key in _calendar_cache
        cached, expiry = _calendar_cache[cache_key]
        assert cached == busy_times
        assert expiry > time.time()

    def test_get_cached_busy_times_valid(self, service):
        """Test retrieving valid cached busy times."""
        busy_times = [{"start": "2024-01-15T10:00:00", "end": "2024-01-15T11:00:00"}]
        cache_key = "calendar_busy:123:test"
        _calendar_cache[cache_key] = (busy_times, time.time() + 100)

        result = service._get_cached_busy_times(cache_key)

        assert result == busy_times

    def test_get_cached_busy_times_expired(self, service):
        """Test retrieving expired cached busy times."""
        busy_times = [{"start": "2024-01-15T10:00:00", "end": "2024-01-15T11:00:00"}]
        cache_key = "calendar_busy:123:test"
        _calendar_cache[cache_key] = (busy_times, time.time() - 1)

        result = service._get_cached_busy_times(cache_key)

        assert result is None
        assert cache_key not in _calendar_cache

    def test_get_cached_busy_times_not_found(self, service):
        """Test retrieving non-existent cached busy times."""
        result = service._get_cached_busy_times("nonexistent_key")
        assert result is None

    def test_cache_cleanup_triggered(self, service):
        """Test cache cleanup is triggered when cache is large."""
        now = time.time()
        for i in range(1001):
            if i < 500:
                _calendar_cache[f"key_{i}"] = ([], now - 1)
            else:
                _calendar_cache[f"key_{i}"] = ([], now + 1000)

        service._cache_busy_times("new_key", [])

        assert len(_calendar_cache) < 1001

    def test_cleanup_cache(self, service):
        """Test explicit cache cleanup."""
        now = time.time()
        _calendar_cache["expired1"] = ([], now - 10)
        _calendar_cache["expired2"] = ([], now - 5)
        _calendar_cache["valid"] = ([], now + 100)

        service._cleanup_cache()

        assert "expired1" not in _calendar_cache
        assert "expired2" not in _calendar_cache
        assert "valid" in _calendar_cache


class TestInvalidateCalendarCache:
    """Tests for cache invalidation function."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test."""
        _calendar_cache.clear()
        yield
        _calendar_cache.clear()

    def test_invalidate_all(self):
        """Test invalidating all cache entries."""
        _calendar_cache["calendar_busy:1:key1"] = ([], time.time())
        _calendar_cache["calendar_busy:2:key2"] = ([], time.time())
        _calendar_cache["calendar_busy:3:key3"] = ([], time.time())

        invalidate_calendar_cache()

        assert len(_calendar_cache) == 0

    def test_invalidate_for_user(self):
        """Test invalidating cache for specific user."""
        _calendar_cache["calendar_busy:123:key1"] = ([], time.time())
        _calendar_cache["calendar_busy:123:key2"] = ([], time.time())
        _calendar_cache["calendar_busy:456:key3"] = ([], time.time())

        invalidate_calendar_cache(user_id=123)

        assert "calendar_busy:123:key1" not in _calendar_cache
        assert "calendar_busy:123:key2" not in _calendar_cache
        assert "calendar_busy:456:key3" in _calendar_cache

    def test_invalidate_user_not_in_cache(self):
        """Test invalidating cache for user with no entries."""
        _calendar_cache["calendar_busy:456:key"] = ([], time.time())

        invalidate_calendar_cache(user_id=123)

        assert "calendar_busy:456:key" in _calendar_cache


class TestTokenRefresh:
    """Tests for token refresh functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return CalendarConflictService(mock_db)

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, service, mock_db):
        """Test successful token refresh."""
        user = MagicMock()
        user.google_calendar_refresh_token = "refresh_token"

        new_tokens = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }

        with patch(
            "core.calendar_conflict.google_calendar.refresh_access_token",
            new_callable=AsyncMock,
            return_value=new_tokens,
        ):
            result = await service._refresh_token(user)

            assert result == "new_access_token"
            assert user.google_calendar_access_token == "new_access_token"
            mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_updates_expiry(self, service, mock_db):
        """Test token refresh updates expiry time."""
        user = MagicMock()
        user.google_calendar_refresh_token = "refresh_token"
        user.google_calendar_token_expires = None

        new_tokens = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }

        with patch(
            "core.calendar_conflict.google_calendar.refresh_access_token",
            new_callable=AsyncMock,
            return_value=new_tokens,
        ):
            await service._refresh_token(user)

            assert user.google_calendar_token_expires is not None
            assert user.google_calendar_token_expires > datetime.now(UTC)


class TestFetchBusyTimes:
    """Tests for fetching busy times from Google Calendar."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance."""
        return CalendarConflictService(mock_db)

    @pytest.fixture
    def mock_user(self):
        """Create mock user with valid tokens."""
        user = MagicMock()
        user.id = 123
        user.google_calendar_access_token = "access_token"
        user.google_calendar_refresh_token = "refresh_token"
        user.google_calendar_token_expires = datetime.now(UTC) + timedelta(hours=1)
        return user

    @pytest.mark.asyncio
    async def test_fetch_busy_times_success(self, service, mock_user):
        """Test successful fetch of busy times."""
        expected_busy = [
            {"start": "2024-01-15T10:00:00Z", "end": "2024-01-15T11:00:00Z"}
        ]
        start = datetime.now(UTC)
        end = start + timedelta(hours=1)

        with patch(
            "core.calendar_conflict.google_calendar.check_busy_times",
            new_callable=AsyncMock,
            return_value=expected_busy,
        ):
            result = await service._fetch_busy_times(mock_user, start, end)

            assert result == expected_busy

    @pytest.mark.asyncio
    async def test_fetch_busy_times_refreshes_expired_token(
        self, service, mock_user
    ):
        """Test that expired token is refreshed before fetch."""
        mock_user.google_calendar_token_expires = datetime.now(UTC) - timedelta(
            minutes=10
        )

        with patch.object(
            service, "_is_token_expired", return_value=True
        ), patch.object(
            service, "_refresh_token", new_callable=AsyncMock
        ) as mock_refresh:
            mock_refresh.return_value = "new_token"
            with patch(
                "core.calendar_conflict.google_calendar.check_busy_times",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await service._fetch_busy_times(
                    mock_user,
                    datetime.now(UTC),
                    datetime.now(UTC) + timedelta(hours=1),
                )

                mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_busy_times_api_error(self, service, mock_user):
        """Test CalendarAPIError is raised on API failure."""
        with patch(
            "core.calendar_conflict.google_calendar.check_busy_times",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ), pytest.raises(CalendarAPIError):
            await service._fetch_busy_times(
                mock_user,
                datetime.now(UTC),
                datetime.now(UTC) + timedelta(hours=1),
            )

    @pytest.mark.asyncio
    async def test_fetch_busy_times_token_refresh_error(self, service, mock_user):
        """Test CalendarAPIError on token refresh failure."""
        with patch.object(service, "_is_token_expired", return_value=True), patch.object(
            service,
            "_refresh_token",
            new_callable=AsyncMock,
            side_effect=Exception("Refresh failed"),
        ), pytest.raises(CalendarAPIError, match="Token refresh failed"):
            await service._fetch_busy_times(
                mock_user,
                datetime.now(UTC),
                datetime.now(UTC) + timedelta(hours=1),
            )
