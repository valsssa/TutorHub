"""Tests for APScheduler background jobs module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetScheduler:
    """Test get_scheduler function."""

    def test_get_scheduler_creates_new_scheduler(self):
        """Test get_scheduler creates scheduler when none exists."""
        from core import scheduler as scheduler_module

        # Reset global scheduler
        scheduler_module.scheduler = None

        sched = scheduler_module.get_scheduler()

        assert sched is not None
        assert scheduler_module.scheduler is sched

    def test_get_scheduler_returns_existing_scheduler(self):
        """Test get_scheduler returns existing scheduler."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from core import scheduler as scheduler_module

        # Set a mock scheduler
        mock_scheduler = AsyncIOScheduler()
        scheduler_module.scheduler = mock_scheduler

        sched = scheduler_module.get_scheduler()

        assert sched is mock_scheduler

        # Cleanup
        scheduler_module.scheduler = None


class TestInitScheduler:
    """Test init_scheduler function."""

    def test_init_scheduler_creates_new_scheduler(self):
        """Test init_scheduler creates and configures new scheduler."""
        from core import scheduler as scheduler_module

        # Reset global scheduler
        scheduler_module.scheduler = None

        with patch.object(scheduler_module, "expire_requests", create=True):
            with patch.object(scheduler_module, "start_sessions", create=True):
                with patch.object(scheduler_module, "end_sessions", create=True):
                    with patch.object(scheduler_module, "retry_zoom_meetings", create=True):
                        with patch.object(scheduler_module, "send_package_expiry_warnings", create=True):
                            with patch.object(scheduler_module, "mark_expired_packages", create=True):
                                with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
                                    mock_sched = MagicMock()
                                    mock_sched.running = False
                                    MockScheduler.return_value = mock_sched

                                    sched = scheduler_module.init_scheduler()

        assert sched is mock_sched
        # Verify jobs were added
        assert mock_sched.add_job.call_count >= 6  # At least 6 jobs

        # Cleanup
        scheduler_module.scheduler = None

    def test_init_scheduler_returns_existing_if_running(self):
        """Test init_scheduler returns existing scheduler if running."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from core import scheduler as scheduler_module

        mock_scheduler = MagicMock(spec=AsyncIOScheduler)
        mock_scheduler.running = True
        scheduler_module.scheduler = mock_scheduler

        result = scheduler_module.init_scheduler()

        assert result is mock_scheduler

        # Cleanup
        scheduler_module.scheduler = None

    def test_init_scheduler_adds_expire_requests_job(self):
        """Test init_scheduler adds expire_requests job."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            # Find the expire_requests job call
            job_ids = [call.kwargs.get("id") for call in mock_sched.add_job.call_args_list]
            assert "expire_requests" in job_ids

        scheduler_module.scheduler = None

    def test_init_scheduler_adds_start_sessions_job(self):
        """Test init_scheduler adds start_sessions job with 1 minute interval."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            job_ids = [call.kwargs.get("id") for call in mock_sched.add_job.call_args_list]
            assert "start_sessions" in job_ids

        scheduler_module.scheduler = None

    def test_init_scheduler_adds_end_sessions_job(self):
        """Test init_scheduler adds end_sessions job."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            job_ids = [call.kwargs.get("id") for call in mock_sched.add_job.call_args_list]
            assert "end_sessions" in job_ids

        scheduler_module.scheduler = None

    def test_init_scheduler_adds_clock_skew_job(self):
        """Test init_scheduler adds clock skew monitoring job."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            job_ids = [call.kwargs.get("id") for call in mock_sched.add_job.call_args_list]
            assert "check_clock_skew" in job_ids

        scheduler_module.scheduler = None

    def test_init_scheduler_adds_package_jobs(self):
        """Test init_scheduler adds package management jobs."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            job_ids = [call.kwargs.get("id") for call in mock_sched.add_job.call_args_list]
            assert "send_package_expiry_warnings" in job_ids
            assert "mark_expired_packages" in job_ids

        scheduler_module.scheduler = None


class TestStartScheduler:
    """Test start_scheduler function."""

    def test_start_scheduler_starts_new_scheduler(self):
        """Test start_scheduler initializes and starts scheduler."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch.object(scheduler_module, "init_scheduler") as mock_init:
            mock_sched = MagicMock()
            mock_sched.running = False
            mock_init.return_value = mock_sched

            with patch.object(scheduler_module, "_startup_clock_skew_check"):
                scheduler_module.start_scheduler()

        mock_sched.start.assert_called_once()

        scheduler_module.scheduler = None

    def test_start_scheduler_does_not_start_if_running(self):
        """Test start_scheduler doesn't start if already running."""
        from core import scheduler as scheduler_module

        mock_sched = MagicMock()
        mock_sched.running = True
        scheduler_module.scheduler = mock_sched

        scheduler_module.start_scheduler()

        mock_sched.start.assert_not_called()

        scheduler_module.scheduler = None

    def test_start_scheduler_performs_clock_skew_check(self):
        """Test start_scheduler performs startup clock skew check."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch.object(scheduler_module, "init_scheduler") as mock_init:
            mock_sched = MagicMock()
            mock_sched.running = False
            mock_init.return_value = mock_sched

            with patch.object(scheduler_module, "_startup_clock_skew_check") as mock_check:
                scheduler_module.start_scheduler()

        mock_check.assert_called_once()

        scheduler_module.scheduler = None


class TestStopScheduler:
    """Test stop_scheduler function."""

    def test_stop_scheduler_stops_running_scheduler(self):
        """Test stop_scheduler stops a running scheduler."""
        from core import scheduler as scheduler_module

        mock_sched = MagicMock()
        mock_sched.running = True
        scheduler_module.scheduler = mock_sched

        scheduler_module.stop_scheduler()

        mock_sched.shutdown.assert_called_once_with(wait=False)

        scheduler_module.scheduler = None

    def test_stop_scheduler_does_nothing_if_not_running(self):
        """Test stop_scheduler does nothing if scheduler not running."""
        from core import scheduler as scheduler_module

        mock_sched = MagicMock()
        mock_sched.running = False
        scheduler_module.scheduler = mock_sched

        scheduler_module.stop_scheduler()

        mock_sched.shutdown.assert_not_called()

        scheduler_module.scheduler = None

    def test_stop_scheduler_handles_none_scheduler(self):
        """Test stop_scheduler handles None scheduler gracefully."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        # Should not raise
        scheduler_module.stop_scheduler()


class TestClockSkewJob:
    """Test _check_clock_skew_job function."""

    def test_check_clock_skew_job_checks_skew(self):
        """Test _check_clock_skew_job calls check_clock_skew."""
        from core.scheduler import _check_clock_skew_job

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.is_within_threshold = True
        mock_result.offset_seconds = 0.5

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", return_value=mock_result) as mock_check:
                _check_clock_skew_job()

        mock_check.assert_called_once()
        mock_db.close.assert_called_once()

    def test_check_clock_skew_job_handles_exception(self):
        """Test _check_clock_skew_job handles exceptions gracefully."""
        from core.scheduler import _check_clock_skew_job

        mock_db = MagicMock()

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", side_effect=Exception("DB Error")):
                # Should not raise
                _check_clock_skew_job()

        mock_db.close.assert_called_once()

    def test_check_clock_skew_job_uses_threshold(self):
        """Test _check_clock_skew_job uses configured threshold."""
        from core import scheduler as scheduler_module
        from core.scheduler import _check_clock_skew_job

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.is_within_threshold = True
        mock_result.offset_seconds = 1.0

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", return_value=mock_result) as mock_check:
                _check_clock_skew_job()

        # Should use CLOCK_SKEW_THRESHOLD_SECONDS
        mock_check.assert_called_once_with(
            mock_db, threshold_seconds=scheduler_module.CLOCK_SKEW_THRESHOLD_SECONDS
        )


class TestStartupClockSkewCheck:
    """Test _startup_clock_skew_check function."""

    def test_startup_clock_skew_check_within_threshold(self):
        """Test _startup_clock_skew_check logs info when within threshold."""
        from core.scheduler import _startup_clock_skew_check

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.is_within_threshold = True
        mock_result.offset_seconds = 0.5

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", return_value=mock_result):
                # Should complete without error
                _startup_clock_skew_check()

        mock_db.close.assert_called_once()

    def test_startup_clock_skew_check_exceeds_threshold(self):
        """Test _startup_clock_skew_check logs warning when threshold exceeded."""
        from core.scheduler import _startup_clock_skew_check

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.is_within_threshold = False
        mock_result.offset_seconds = 10.0

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", return_value=mock_result):
                with patch("core.scheduler.logger") as mock_logger:
                    _startup_clock_skew_check()

        mock_logger.warning.assert_called()
        mock_db.close.assert_called_once()

    def test_startup_clock_skew_check_handles_exception(self):
        """Test _startup_clock_skew_check handles exceptions gracefully."""
        from core.scheduler import _startup_clock_skew_check

        mock_db = MagicMock()

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", side_effect=Exception("DB Error")):
                # Should not raise
                _startup_clock_skew_check()

        mock_db.close.assert_called_once()

    def test_startup_clock_skew_check_offset_direction(self):
        """Test _startup_clock_skew_check reports correct offset direction."""
        from core.scheduler import _startup_clock_skew_check

        mock_db = MagicMock()

        # Test positive offset (app ahead)
        mock_result_ahead = MagicMock()
        mock_result_ahead.is_within_threshold = False
        mock_result_ahead.offset_seconds = 10.0

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", return_value=mock_result_ahead):
                with patch("core.scheduler.logger") as mock_logger:
                    _startup_clock_skew_check()

        # Should mention "ahead of"
        warning_call = mock_logger.warning.call_args
        assert "ahead of" in str(warning_call)

        # Test negative offset (app behind)
        mock_result_behind = MagicMock()
        mock_result_behind.is_within_threshold = False
        mock_result_behind.offset_seconds = -10.0

        with patch("core.scheduler.SessionLocal", return_value=mock_db):
            with patch("core.scheduler.check_clock_skew", return_value=mock_result_behind):
                with patch("core.scheduler.logger") as mock_logger:
                    _startup_clock_skew_check()

        # Should mention "behind"
        warning_call = mock_logger.warning.call_args
        assert "behind" in str(warning_call)


class TestLifespanScheduler:
    """Test lifespan_scheduler context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_scheduler_starts_on_enter(self):
        """Test lifespan_scheduler starts scheduler on enter."""
        from core.scheduler import lifespan_scheduler

        mock_app = MagicMock()

        with patch("core.scheduler.start_scheduler") as mock_start, patch("core.scheduler.stop_scheduler"):
            async with lifespan_scheduler(mock_app):
                mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_scheduler_stops_on_exit(self):
        """Test lifespan_scheduler stops scheduler on exit."""
        from core.scheduler import lifespan_scheduler

        mock_app = MagicMock()

        with patch("core.scheduler.start_scheduler"), patch("core.scheduler.stop_scheduler") as mock_stop:
            async with lifespan_scheduler(mock_app):
                pass

        mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_scheduler_stops_on_exception(self):
        """Test lifespan_scheduler stops scheduler even on exception."""
        from core.scheduler import lifespan_scheduler

        mock_app = MagicMock()

        with patch("core.scheduler.start_scheduler"), patch("core.scheduler.stop_scheduler") as mock_stop:
            try:
                async with lifespan_scheduler(mock_app):
                    raise RuntimeError("Test exception")
            except RuntimeError:
                pass

        mock_stop.assert_called_once()


class TestSchedulerConfiguration:
    """Test scheduler configuration constants."""

    def test_clock_skew_check_interval(self):
        """Test CLOCK_SKEW_CHECK_INTERVAL_MINUTES is set."""
        from core.scheduler import CLOCK_SKEW_CHECK_INTERVAL_MINUTES

        assert CLOCK_SKEW_CHECK_INTERVAL_MINUTES == 5

    def test_clock_skew_threshold(self):
        """Test CLOCK_SKEW_THRESHOLD_SECONDS is set."""
        from core.scheduler import CLOCK_SKEW_THRESHOLD_SECONDS

        assert CLOCK_SKEW_THRESHOLD_SECONDS == 5


class TestJobConfiguration:
    """Test job configuration in init_scheduler."""

    def test_all_jobs_have_max_instances_1(self):
        """Test all jobs are configured with max_instances=1."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            for call in mock_sched.add_job.call_args_list:
                assert call.kwargs.get("max_instances") == 1

        scheduler_module.scheduler = None

    def test_all_jobs_have_replace_existing_true(self):
        """Test all jobs are configured with replace_existing=True."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            for call in mock_sched.add_job.call_args_list:
                assert call.kwargs.get("replace_existing") is True

        scheduler_module.scheduler = None

    def test_all_jobs_have_unique_ids(self):
        """Test all jobs have unique IDs."""
        from core import scheduler as scheduler_module

        scheduler_module.scheduler = None

        with patch("core.scheduler.AsyncIOScheduler") as MockScheduler:
            mock_sched = MagicMock()
            mock_sched.running = False
            MockScheduler.return_value = mock_sched

            with patch("modules.bookings.jobs.expire_requests"):
                with patch("modules.bookings.jobs.start_sessions"):
                    with patch("modules.bookings.jobs.end_sessions"):
                        with patch("modules.bookings.jobs.retry_zoom_meetings"):
                            with patch("modules.packages.jobs.send_package_expiry_warnings"):
                                with patch("modules.packages.jobs.mark_expired_packages"):
                                    scheduler_module.init_scheduler()

            job_ids = [call.kwargs.get("id") for call in mock_sched.add_job.call_args_list]
            assert len(job_ids) == len(set(job_ids))  # All unique

        scheduler_module.scheduler = None
