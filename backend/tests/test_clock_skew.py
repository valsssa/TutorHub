"""Tests for clock skew detection and monitoring."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from core.clock_skew import (
    DEFAULT_SKEW_THRESHOLD_SECONDS,
    SKEW_CHECK_INTERVAL_SECONDS,
    ClockSkewMonitor,
    ClockSkewResult,
    check_clock_skew,
    get_db_time,
    get_job_skew_monitor,
)


class TestClockSkewResult:
    """Tests for ClockSkewResult named tuple."""

    def test_create_result(self):
        """Test creating a ClockSkewResult."""
        app_time = datetime.now(UTC)
        db_time = datetime.now(UTC)
        result = ClockSkewResult(
            app_time=app_time,
            db_time=db_time,
            offset_seconds=0.5,
            is_within_threshold=True,
        )

        assert result.app_time == app_time
        assert result.db_time == db_time
        assert result.offset_seconds == 0.5
        assert result.is_within_threshold is True

    def test_result_is_named_tuple(self):
        """Test ClockSkewResult is a named tuple."""
        result = ClockSkewResult(
            app_time=datetime.now(UTC),
            db_time=datetime.now(UTC),
            offset_seconds=0.0,
            is_within_threshold=True,
        )

        assert hasattr(result, "_fields")
        assert "app_time" in result._fields
        assert "db_time" in result._fields
        assert "offset_seconds" in result._fields
        assert "is_within_threshold" in result._fields


class TestGetDbTime:
    """Tests for get_db_time function."""

    def test_get_db_time(self):
        """Test getting database time."""
        mock_db = MagicMock()
        mock_time = datetime(2024, 1, 15, 10, 30, 0)
        mock_db.execute.return_value.scalar.return_value = mock_time

        result = get_db_time(mock_db)

        assert result.tzinfo == UTC
        mock_db.execute.assert_called_once()

    def test_get_db_time_already_has_timezone(self):
        """Test get_db_time when result already has timezone."""
        mock_db = MagicMock()
        mock_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        mock_db.execute.return_value.scalar.return_value = mock_time

        result = get_db_time(mock_db)

        assert result.tzinfo == UTC
        assert result == mock_time


class TestCheckClockSkew:
    """Tests for check_clock_skew function."""

    def test_check_within_threshold(self):
        """Test clock skew within threshold."""
        mock_db = MagicMock()
        now = datetime.now(UTC)
        mock_db.execute.return_value.scalar.return_value = now

        with patch("core.clock_skew.datetime") as mock_datetime:
            mock_datetime.now.return_value = now + timedelta(seconds=2)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            result = check_clock_skew(mock_db, threshold_seconds=5)

        assert result.is_within_threshold is True
        assert abs(result.offset_seconds) <= 5

    def test_check_exceeds_threshold(self):
        """Test clock skew exceeds threshold."""
        mock_db = MagicMock()
        db_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        mock_db.execute.return_value.scalar.return_value = db_time

        with patch("core.clock_skew.datetime") as mock_datetime:
            app_time = db_time + timedelta(seconds=10)
            mock_datetime.now.return_value = app_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            result = check_clock_skew(mock_db, threshold_seconds=5)

        assert result.is_within_threshold is False
        assert result.offset_seconds > 5

    def test_check_app_behind_db(self):
        """Test when app time is behind database time."""
        mock_db = MagicMock()
        db_time = datetime(2024, 1, 15, 10, 0, 10, tzinfo=UTC)
        mock_db.execute.return_value.scalar.return_value = db_time

        with patch("core.clock_skew.datetime") as mock_datetime:
            app_time = db_time - timedelta(seconds=10)
            mock_datetime.now.return_value = app_time

            result = check_clock_skew(mock_db, threshold_seconds=5)

        assert result.offset_seconds < 0
        assert result.is_within_threshold is False

    def test_check_uses_default_threshold(self):
        """Test default threshold is used."""
        mock_db = MagicMock()
        now = datetime.now(UTC)
        mock_db.execute.return_value.scalar.return_value = now

        with patch("core.clock_skew.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            result = check_clock_skew(mock_db)

        assert result.is_within_threshold is True

    def test_check_logs_warning_on_skew(self):
        """Test warning is logged when skew exceeds threshold."""
        mock_db = MagicMock()
        db_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        mock_db.execute.return_value.scalar.return_value = db_time

        with patch("core.clock_skew.datetime") as mock_datetime:
            mock_datetime.now.return_value = db_time + timedelta(seconds=20)

            with patch("core.clock_skew.logger") as mock_logger:
                check_clock_skew(mock_db, threshold_seconds=5)
                mock_logger.warning.assert_called_once()


class TestClockSkewMonitor:
    """Tests for ClockSkewMonitor class."""

    def test_init_default_values(self):
        """Test monitor initializes with default values."""
        monitor = ClockSkewMonitor()

        assert monitor.threshold_seconds == DEFAULT_SKEW_THRESHOLD_SECONDS
        assert monitor.check_interval_seconds == SKEW_CHECK_INTERVAL_SECONDS
        assert monitor._last_check_time is None
        assert monitor._last_skew_result is None

    def test_init_custom_values(self):
        """Test monitor initializes with custom values."""
        monitor = ClockSkewMonitor(threshold_seconds=10, check_interval_seconds=60)

        assert monitor.threshold_seconds == 10
        assert monitor.check_interval_seconds == 60

    def test_should_check_first_time(self):
        """Test should_check returns True on first call."""
        monitor = ClockSkewMonitor()

        assert monitor.should_check() is True

    def test_should_check_after_interval(self):
        """Test should_check returns True after interval elapsed."""
        monitor = ClockSkewMonitor(check_interval_seconds=60)
        monitor._last_check_time = datetime.now(UTC) - timedelta(seconds=120)

        assert monitor.should_check() is True

    def test_should_check_before_interval(self):
        """Test should_check returns False before interval elapsed."""
        monitor = ClockSkewMonitor(check_interval_seconds=60)
        monitor._last_check_time = datetime.now(UTC) - timedelta(seconds=30)

        assert monitor.should_check() is False

    def test_check_and_warn_performs_check(self):
        """Test check_and_warn performs a check when due."""
        monitor = ClockSkewMonitor()
        mock_db = MagicMock()

        with patch("core.clock_skew.check_clock_skew") as mock_check:
            mock_result = ClockSkewResult(
                app_time=datetime.now(UTC),
                db_time=datetime.now(UTC),
                offset_seconds=0.5,
                is_within_threshold=True,
            )
            mock_check.return_value = mock_result

            result = monitor.check_and_warn(mock_db)

            assert result == mock_result
            mock_check.assert_called_once_with(mock_db, monitor.threshold_seconds)

    def test_check_and_warn_skips_when_not_due(self):
        """Test check_and_warn skips check when not due."""
        monitor = ClockSkewMonitor(check_interval_seconds=60)
        monitor._last_check_time = datetime.now(UTC) - timedelta(seconds=30)
        monitor._last_skew_result = ClockSkewResult(
            app_time=datetime.now(UTC),
            db_time=datetime.now(UTC),
            offset_seconds=0.5,
            is_within_threshold=True,
        )

        mock_db = MagicMock()

        with patch("core.clock_skew.check_clock_skew") as mock_check:
            result = monitor.check_and_warn(mock_db)

            assert result == monitor._last_skew_result
            mock_check.assert_not_called()

    def test_check_and_warn_updates_last_check_time(self):
        """Test check_and_warn updates last check time."""
        monitor = ClockSkewMonitor()
        mock_db = MagicMock()

        with patch("core.clock_skew.check_clock_skew") as mock_check:
            mock_check.return_value = ClockSkewResult(
                app_time=datetime.now(UTC),
                db_time=datetime.now(UTC),
                offset_seconds=0.5,
                is_within_threshold=True,
            )

            before = datetime.now(UTC)
            monitor.check_and_warn(mock_db)
            after = datetime.now(UTC)

            assert monitor._last_check_time >= before
            assert monitor._last_check_time <= after

    def test_check_and_warn_stores_result(self):
        """Test check_and_warn stores the result."""
        monitor = ClockSkewMonitor()
        mock_db = MagicMock()

        expected_result = ClockSkewResult(
            app_time=datetime.now(UTC),
            db_time=datetime.now(UTC),
            offset_seconds=2.5,
            is_within_threshold=True,
        )

        with patch("core.clock_skew.check_clock_skew", return_value=expected_result):
            monitor.check_and_warn(mock_db)

            assert monitor._last_skew_result == expected_result

    def test_last_offset_none_initially(self):
        """Test last_offset is None initially."""
        monitor = ClockSkewMonitor()

        assert monitor.last_offset is None

    def test_last_offset_returns_value(self):
        """Test last_offset returns stored value."""
        monitor = ClockSkewMonitor()
        monitor._last_skew_result = ClockSkewResult(
            app_time=datetime.now(UTC),
            db_time=datetime.now(UTC),
            offset_seconds=3.5,
            is_within_threshold=True,
        )

        assert monitor.last_offset == 3.5


class TestGetJobSkewMonitor:
    """Tests for get_job_skew_monitor function."""

    def test_returns_monitor_instance(self):
        """Test function returns a ClockSkewMonitor."""
        with patch("core.clock_skew._job_skew_monitor", None):
            monitor = get_job_skew_monitor()

            assert isinstance(monitor, ClockSkewMonitor)

    def test_returns_same_instance(self):
        """Test function returns the same instance on repeated calls."""
        monitor1 = get_job_skew_monitor()
        monitor2 = get_job_skew_monitor()

        assert monitor1 is monitor2


class TestConstants:
    """Tests for module constants."""

    def test_default_threshold(self):
        """Test default skew threshold value."""
        assert DEFAULT_SKEW_THRESHOLD_SECONDS == 5

    def test_check_interval(self):
        """Test check interval value."""
        assert SKEW_CHECK_INTERVAL_SECONDS == 300


class TestIntegration:
    """Integration tests for clock skew functionality."""

    def test_monitor_with_check_skew(self):
        """Test monitor integration with check_clock_skew."""
        monitor = ClockSkewMonitor(threshold_seconds=10)
        mock_db = MagicMock()
        now = datetime.now(UTC)
        mock_db.execute.return_value.scalar.return_value = now

        with patch("core.clock_skew.datetime") as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            result = monitor.check_and_warn(mock_db)

            assert result is not None
            assert result.is_within_threshold is True

    def test_typical_background_job_usage(self):
        """Test typical usage pattern in background jobs."""
        monitor = ClockSkewMonitor(threshold_seconds=5, check_interval_seconds=300)
        mock_db = MagicMock()
        now = datetime.now(UTC)
        mock_db.execute.return_value.scalar.return_value = now

        with patch("core.clock_skew.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            result = monitor.check_and_warn(mock_db)

            if result and result.is_within_threshold:
                db_time = get_db_time(mock_db)
                assert db_time is not None
