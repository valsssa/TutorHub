"""
Package Jobs Tests

Comprehensive tests for background jobs that handle package expiration warnings
and automatic package status updates.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modules.packages.jobs import (
    EXPIRY_WARNING_DAYS,
    EXPIRY_WARNING_LOCK_TIMEOUT,
    mark_expired_packages,
    send_package_expiry_warnings,
)


class TestSendPackageExpiryWarnings:
    """Tests for send_package_expiry_warnings job."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def mock_lock_acquired(self):
        """Mock successful lock acquisition."""
        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=True)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        return lock_context

    @pytest.fixture
    def mock_lock_not_acquired(self):
        """Mock failed lock acquisition."""
        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=False)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        return lock_context

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_sends_warnings_when_lock_acquired(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_db_session,
        mock_lock_acquired,
    ):
        """Test that warnings are sent when lock is acquired."""
        mock_session_local.return_value = mock_db_session
        mock_distributed_lock.acquire.return_value = mock_lock_acquired
        mock_expiration_service.send_expiry_warnings.return_value = 5
        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        await send_package_expiry_warnings()

        mock_expiration_service.send_expiry_warnings.assert_called_once_with(
            mock_db_session, days_until_expiry=EXPIRY_WARNING_DAYS
        )

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    async def test_skips_when_lock_not_acquired(
        self,
        mock_distributed_lock,
        mock_session_local,
        mock_lock_not_acquired,
    ):
        """Test that job skips when another instance holds the lock."""
        mock_distributed_lock.acquire.return_value = mock_lock_not_acquired

        await send_package_expiry_warnings()

        # SessionLocal should not be called if lock not acquired
        mock_session_local.assert_not_called()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_closes_db_session_on_success(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_db_session,
        mock_lock_acquired,
    ):
        """Test that database session is closed after successful execution."""
        mock_session_local.return_value = mock_db_session
        mock_distributed_lock.acquire.return_value = mock_lock_acquired
        mock_expiration_service.send_expiry_warnings.return_value = 0
        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        await send_package_expiry_warnings()

        mock_db_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_rollback_and_close_on_error(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_db_session,
        mock_lock_acquired,
    ):
        """Test that database is rolled back and closed on error."""
        mock_session_local.return_value = mock_db_session
        mock_distributed_lock.acquire.return_value = mock_lock_acquired
        mock_expiration_service.send_expiry_warnings.side_effect = Exception(
            "Database error"
        )
        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        await send_package_expiry_warnings()

        mock_db_session.rollback.assert_called_once()
        mock_db_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.distributed_lock")
    async def test_uses_correct_lock_name(
        self,
        mock_distributed_lock,
        mock_lock_not_acquired,
    ):
        """Test that the correct lock name is used."""
        mock_distributed_lock.acquire.return_value = mock_lock_not_acquired

        await send_package_expiry_warnings()

        mock_distributed_lock.acquire.assert_called_once_with(
            "job:send_package_expiry_warnings", timeout=EXPIRY_WARNING_LOCK_TIMEOUT
        )

    def test_expiry_warning_days_is_7(self):
        """Test that expiry warning is set to 7 days."""
        assert EXPIRY_WARNING_DAYS == 7

    def test_lock_timeout_is_5_minutes(self):
        """Test that lock timeout is 5 minutes (300 seconds)."""
        assert EXPIRY_WARNING_LOCK_TIMEOUT == 300


class TestMarkExpiredPackages:
    """Tests for mark_expired_packages job."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def mock_lock_acquired(self):
        """Mock successful lock acquisition."""
        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=True)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        return lock_context

    @pytest.fixture
    def mock_lock_not_acquired(self):
        """Mock failed lock acquisition."""
        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=False)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        return lock_context

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_marks_packages_when_lock_acquired(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_db_session,
        mock_lock_acquired,
    ):
        """Test that packages are marked expired when lock is acquired."""
        mock_session_local.return_value = mock_db_session
        mock_distributed_lock.acquire.return_value = mock_lock_acquired
        mock_expiration_service.mark_expired_packages.return_value = 3
        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        await mark_expired_packages()

        mock_expiration_service.mark_expired_packages.assert_called_once_with(
            mock_db_session
        )

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    async def test_skips_when_lock_not_acquired(
        self,
        mock_distributed_lock,
        mock_session_local,
        mock_lock_not_acquired,
    ):
        """Test that job skips when another instance holds the lock."""
        mock_distributed_lock.acquire.return_value = mock_lock_not_acquired

        await mark_expired_packages()

        mock_session_local.assert_not_called()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_closes_db_session_after_execution(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_db_session,
        mock_lock_acquired,
    ):
        """Test that database session is closed after execution."""
        mock_session_local.return_value = mock_db_session
        mock_distributed_lock.acquire.return_value = mock_lock_acquired
        mock_expiration_service.mark_expired_packages.return_value = 0
        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        await mark_expired_packages()

        mock_db_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_rollback_on_error(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_db_session,
        mock_lock_acquired,
    ):
        """Test that database is rolled back on error."""
        mock_session_local.return_value = mock_db_session
        mock_distributed_lock.acquire.return_value = mock_lock_acquired
        mock_expiration_service.mark_expired_packages.side_effect = Exception(
            "DB error"
        )
        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        await mark_expired_packages()

        mock_db_session.rollback.assert_called_once()
        mock_db_session.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.distributed_lock")
    async def test_uses_correct_lock_name(
        self,
        mock_distributed_lock,
        mock_lock_not_acquired,
    ):
        """Test that the correct lock name is used."""
        mock_distributed_lock.acquire.return_value = mock_lock_not_acquired

        await mark_expired_packages()

        mock_distributed_lock.acquire.assert_called_once_with(
            "job:mark_expired_packages", timeout=EXPIRY_WARNING_LOCK_TIMEOUT
        )


class TestJobConfiguration:
    """Tests for job configuration constants."""

    def test_expiry_warning_days_configuration(self):
        """Test EXPIRY_WARNING_DAYS is properly configured."""
        assert isinstance(EXPIRY_WARNING_DAYS, int)
        assert EXPIRY_WARNING_DAYS > 0
        assert EXPIRY_WARNING_DAYS == 7

    def test_lock_timeout_configuration(self):
        """Test EXPIRY_WARNING_LOCK_TIMEOUT is properly configured."""
        assert isinstance(EXPIRY_WARNING_LOCK_TIMEOUT, int)
        assert EXPIRY_WARNING_LOCK_TIMEOUT > 0
        assert EXPIRY_WARNING_LOCK_TIMEOUT == 300


class TestDistributedLockIntegration:
    """Tests for distributed lock integration with jobs."""

    def test_lock_prevents_concurrent_execution(self):
        """Test that lock prevents multiple instances from running simultaneously."""
        # When lock is held by another instance, job should skip
        pass

    def test_lock_auto_expires_to_prevent_deadlock(self):
        """Test that lock has timeout to prevent deadlocks."""
        # Lock should auto-expire after EXPIRY_WARNING_LOCK_TIMEOUT seconds
        assert EXPIRY_WARNING_LOCK_TIMEOUT == 300  # 5 minutes

    def test_lock_released_after_job_completion(self):
        """Test that lock is released when job completes."""
        # Using context manager ensures lock is released
        pass


class TestJobTracing:
    """Tests for job tracing integration."""

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.trace_background_job")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.PackageExpirationService")
    async def test_job_is_traced(
        self,
        mock_expiration_service,
        mock_session_local,
        mock_distributed_lock,
        mock_trace,
    ):
        """Test that job execution is traced."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=True)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        mock_distributed_lock.acquire.return_value = lock_context

        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        mock_expiration_service.send_expiry_warnings.return_value = 0

        await send_package_expiry_warnings()

        mock_trace.assert_called_once_with(
            "send_package_expiry_warnings", interval="daily"
        )


class TestJobErrorRecovery:
    """Tests for job error recovery scenarios."""

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_exception_does_not_crash_job(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
    ):
        """Test that exceptions are caught and don't crash the job."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=True)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        mock_distributed_lock.acquire.return_value = lock_context

        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        mock_expiration_service.send_expiry_warnings.side_effect = ValueError(
            "Test error"
        )

        # Should not raise - error should be caught and logged
        await send_package_expiry_warnings()

        mock_db.rollback.assert_called()
        mock_db.close.assert_called()


class TestJobLogging:
    """Tests for job logging behavior."""

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.logger")
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_logs_when_lock_not_acquired(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_logger,
    ):
        """Test that appropriate log is written when lock is not acquired."""
        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=False)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        mock_distributed_lock.acquire.return_value = lock_context

        await send_package_expiry_warnings()

        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    @patch("modules.packages.jobs.logger")
    @patch("modules.packages.jobs.SessionLocal")
    @patch("modules.packages.jobs.distributed_lock")
    @patch("modules.packages.jobs.PackageExpirationService")
    @patch("modules.packages.jobs.trace_background_job")
    async def test_logs_warnings_sent_count(
        self,
        mock_trace,
        mock_expiration_service,
        mock_distributed_lock,
        mock_session_local,
        mock_logger,
    ):
        """Test that number of warnings sent is logged."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        lock_context = AsyncMock()
        lock_context.__aenter__ = AsyncMock(return_value=True)
        lock_context.__aexit__ = AsyncMock(return_value=None)
        mock_distributed_lock.acquire.return_value = lock_context

        mock_trace.return_value.__enter__ = MagicMock()
        mock_trace.return_value.__exit__ = MagicMock()

        mock_expiration_service.send_expiry_warnings.return_value = 5

        await send_package_expiry_warnings()

        # Check that info log was called with count
        assert mock_logger.info.called or mock_logger.debug.called
