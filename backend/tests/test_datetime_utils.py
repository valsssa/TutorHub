"""Tests for datetime utility functions."""
from datetime import UTC, datetime, timezone

import pytest

from core.datetime_utils import ensure_utc, is_aware, utc_now


class TestUtcNow:
    def test_returns_timezone_aware_datetime(self):
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == UTC

    def test_returns_current_time(self):
        before = utc_now()
        result = utc_now()
        after = utc_now()
        assert before <= result <= after


class TestIsAware:
    def test_aware_datetime_returns_true(self):
        aware = utc_now()
        assert is_aware(aware) is True

    def test_naive_datetime_returns_false(self):
        naive = datetime.now()
        assert is_aware(naive) is False


class TestEnsureUtc:
    def test_aware_utc_returns_unchanged(self):
        dt = utc_now()
        result = ensure_utc(dt)
        assert result == dt

    def test_naive_datetime_raises_error(self):
        naive = datetime.now()
        with pytest.raises(ValueError, match="naive datetime"):
            ensure_utc(naive)
