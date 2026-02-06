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
        before = datetime.now(UTC)
        result = utc_now()
        after = datetime.now(UTC)
        assert before <= result <= after


class TestIsAware:
    def test_aware_datetime_returns_true(self):
        aware = datetime.now(UTC)
        assert is_aware(aware) is True

    def test_naive_datetime_returns_false(self):
        naive = datetime.utcnow()
        assert is_aware(naive) is False


class TestEnsureUtc:
    def test_aware_utc_returns_unchanged(self):
        dt = datetime.now(UTC)
        result = ensure_utc(dt)
        assert result == dt

    def test_naive_datetime_raises_error(self):
        naive = datetime.utcnow()
        with pytest.raises(ValueError, match="naive datetime"):
            ensure_utc(naive)
