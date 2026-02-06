"""Tests for datetime utility functions."""
from datetime import datetime, timezone

import pytest

from core.datetime_utils import utc_now, is_aware, ensure_utc


class TestUtcNow:
    def test_returns_timezone_aware_datetime(self):
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self):
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after


class TestIsAware:
    def test_aware_datetime_returns_true(self):
        aware = datetime.now(timezone.utc)
        assert is_aware(aware) is True

    def test_naive_datetime_returns_false(self):
        naive = datetime.utcnow()
        assert is_aware(naive) is False


class TestEnsureUtc:
    def test_aware_utc_returns_unchanged(self):
        dt = datetime.now(timezone.utc)
        result = ensure_utc(dt)
        assert result == dt

    def test_naive_datetime_raises_error(self):
        naive = datetime.utcnow()
        with pytest.raises(ValueError, match="naive datetime"):
            ensure_utc(naive)
