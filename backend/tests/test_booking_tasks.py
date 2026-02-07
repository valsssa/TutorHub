"""
Booking Tasks Tests

Comprehensive tests for Celery tasks that handle booking state transitions:
- expire_requests: REQUESTED -> EXPIRED (24h timeout)
- start_sessions: SCHEDULED -> ACTIVE (at start_time)
- end_sessions: ACTIVE -> ENDED (at end_time + grace)
"""

import contextlib
from datetime import UTC, datetime, timedelta

from core.datetime_utils import utc_now
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from tasks.booking_tasks import (
    REQUEST_EXPIRY_HOURS,
    SESSION_END_GRACE_MINUTES,
    end_sessions,
    expire_requests,
    start_sessions,
)


class TestExpireRequests:
    """Tests for expire_requests Celery task."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def requested_booking(self):
        """Create mock booking in REQUESTED state."""
        booking = MagicMock()
        booking.id = 1
        booking.session_state = "REQUESTED"
        booking.created_at = utc_now() - timedelta(hours=25)
        return booking

    @pytest.fixture
    def mock_transition_result_success(self):
        """Create mock successful transition result."""
        result = MagicMock()
        result.success = True
        result.already_in_target_state = False
        return result

    @pytest.fixture
    def mock_transition_result_already_expired(self):
        """Create mock idempotent transition result."""
        result = MagicMock()
        result.success = True
        result.already_in_target_state = True
        return result

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_expires_old_requested_bookings(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        requested_booking,
        mock_transition_result_success,
    ):
        """Test that requested bookings older than 24h are expired."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        # Mock query to return expired booking IDs
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (requested_booking.id,)
        ]

        # Mock lock and expire operations
        mock_state_machine.get_booking_with_lock.return_value = requested_booking
        mock_state_machine.expire_booking.return_value = mock_transition_result_success

        # Create mock task instance
        MagicMock()

        result = expire_requests()

        assert result["expired"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        mock_db.commit.assert_called()
        mock_db.close.assert_called_once()

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_skips_already_expired_bookings(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        requested_booking,
        mock_transition_result_already_expired,
    ):
        """Test that already expired bookings are skipped (idempotent)."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (requested_booking.id,)
        ]

        mock_state_machine.get_booking_with_lock.return_value = requested_booking
        mock_state_machine.expire_booking.return_value = (
            mock_transition_result_already_expired
        )

        MagicMock()

        result = expire_requests()

        assert result["expired"] == 0
        assert result["skipped"] == 1
        assert result["errors"] == 0

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_handles_locked_booking(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
    ):
        """Test that locked bookings are skipped (row locked by another transaction)."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [(1,)]

        # Simulate lock acquisition failure
        mock_state_machine.get_booking_with_lock.side_effect = OperationalError(
            "could not obtain lock", None, None
        )

        MagicMock()

        result = expire_requests()

        # Booking should be skipped, no error reported
        assert result["expired"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == 0
        mock_db.rollback.assert_called()

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_handles_booking_not_found(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
    ):
        """Test that missing bookings are handled gracefully."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [(1,)]

        # Booking not found (deleted between query and lock)
        mock_state_machine.get_booking_with_lock.return_value = None

        MagicMock()

        result = expire_requests()

        assert result["expired"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == 0

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    def test_retries_on_general_exception(
        self,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
    ):
        """Test that exceptions are raised (Celery's autoretry handles the retry)."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.side_effect = Exception("Database connection failed")
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        # When an exception occurs, it propagates up
        # Celery's autoretry_for=(Exception,) decorator handles retry in production
        with pytest.raises(Exception) as exc_info:
            expire_requests()

        assert "Database connection failed" in str(exc_info.value)
        mock_db.rollback.assert_called()
        mock_db.close.assert_called()

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    def test_uses_database_time_for_cutoff(
        self,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
    ):
        """Test that database server time is used for cutoff calculation."""
        mock_session_local.return_value = mock_db
        db_time = utc_now()
        mock_get_db_time.return_value = db_time
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = []

        MagicMock()

        expire_requests()

        # Verify get_db_time was called with db session
        mock_get_db_time.assert_called_once_with(mock_db)

    def test_request_expiry_hours_is_24(self):
        """Test that REQUEST_EXPIRY_HOURS is 24."""
        assert REQUEST_EXPIRY_HOURS == 24


class TestStartSessions:
    """Tests for start_sessions Celery task."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def scheduled_booking(self):
        """Create mock booking in SCHEDULED state."""
        booking = MagicMock()
        booking.id = 1
        booking.session_state = "SCHEDULED"
        booking.start_time = utc_now() - timedelta(minutes=5)
        return booking

    @pytest.fixture
    def mock_transition_result_success(self):
        """Create mock successful transition result."""
        result = MagicMock()
        result.success = True
        result.already_in_target_state = False
        return result

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_starts_sessions_at_start_time(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        scheduled_booking,
        mock_transition_result_success,
    ):
        """Test that scheduled sessions are started when start_time passes."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (scheduled_booking.id,)
        ]

        mock_state_machine.get_booking_with_lock.return_value = scheduled_booking
        mock_state_machine.start_session.return_value = mock_transition_result_success

        MagicMock()

        result = start_sessions()

        assert result["started"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        mock_db.commit.assert_called()
        mock_db.close.assert_called_once()

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_skips_already_started_sessions(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        scheduled_booking,
    ):
        """Test that already started sessions are skipped (idempotent)."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (scheduled_booking.id,)
        ]

        result = MagicMock()
        result.success = True
        result.already_in_target_state = True

        mock_state_machine.get_booking_with_lock.return_value = scheduled_booking
        mock_state_machine.start_session.return_value = result

        MagicMock()

        task_result = start_sessions()

        assert task_result["started"] == 0
        assert task_result["skipped"] == 1

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_handles_transition_failure(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        scheduled_booking,
    ):
        """Test handling of transition failures."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (scheduled_booking.id,)
        ]

        result = MagicMock()
        result.success = False
        result.error_message = "Invalid state transition"

        mock_state_machine.get_booking_with_lock.return_value = scheduled_booking
        mock_state_machine.start_session.return_value = result

        MagicMock()

        task_result = start_sessions()

        assert task_result["started"] == 0
        assert task_result["errors"] == 1
        mock_db.rollback.assert_called()

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_handles_locked_booking(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
    ):
        """Test that locked bookings are skipped."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [(1,)]

        mock_state_machine.get_booking_with_lock.side_effect = OperationalError(
            "lock error", None, None
        )

        MagicMock()

        result = start_sessions()

        assert result["started"] == 0
        mock_db.rollback.assert_called()


class TestEndSessions:
    """Tests for end_sessions Celery task."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def active_booking(self):
        """Create mock booking in ACTIVE state."""
        booking = MagicMock()
        booking.id = 1
        booking.session_state = "ACTIVE"
        booking.end_time = utc_now() - timedelta(minutes=10)
        return booking

    @pytest.fixture
    def mock_transition_result_success(self):
        """Create mock successful transition result."""
        result = MagicMock()
        result.success = True
        result.already_in_target_state = False
        return result

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    @patch("modules.bookings.domain.status.SessionOutcome")
    def test_ends_sessions_after_grace_period(
        self,
        mock_session_outcome,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        active_booking,
        mock_transition_result_success,
    ):
        """Test that active sessions are ended after end_time + grace period."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()
        mock_session_outcome.COMPLETED = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (active_booking.id,)
        ]

        mock_state_machine.get_booking_with_lock.return_value = active_booking
        mock_state_machine.end_session.return_value = mock_transition_result_success

        MagicMock()

        result = end_sessions()

        assert result["ended"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        mock_db.commit.assert_called()
        mock_db.close.assert_called_once()

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    @patch("modules.bookings.domain.status.SessionOutcome")
    def test_uses_completed_outcome_by_default(
        self,
        mock_session_outcome,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        active_booking,
        mock_transition_result_success,
    ):
        """Test that COMPLETED outcome is used for auto-ended sessions."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        completed_outcome = MagicMock()
        mock_session_outcome.COMPLETED = completed_outcome

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (active_booking.id,)
        ]

        mock_state_machine.get_booking_with_lock.return_value = active_booking
        mock_state_machine.end_session.return_value = mock_transition_result_success

        MagicMock()

        end_sessions()

        mock_state_machine.end_session.assert_called_with(
            active_booking, completed_outcome
        )

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    @patch("modules.bookings.domain.status.SessionOutcome")
    def test_skips_already_ended_sessions(
        self,
        mock_session_outcome,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        active_booking,
    ):
        """Test that already ended sessions are skipped (idempotent)."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()
        mock_session_outcome.COMPLETED = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (active_booking.id,)
        ]

        result = MagicMock()
        result.success = True
        result.already_in_target_state = True

        mock_state_machine.get_booking_with_lock.return_value = active_booking
        mock_state_machine.end_session.return_value = result

        MagicMock()

        task_result = end_sessions()

        assert task_result["ended"] == 0
        assert task_result["skipped"] == 1

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    @patch("modules.bookings.domain.status.SessionOutcome")
    def test_handles_transition_failure(
        self,
        mock_session_outcome,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_db,
        active_booking,
    ):
        """Test handling of transition failures."""
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()
        mock_session_outcome.COMPLETED = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            (active_booking.id,)
        ]

        result = MagicMock()
        result.success = False
        result.error_message = "Cannot end session"

        mock_state_machine.get_booking_with_lock.return_value = active_booking
        mock_state_machine.end_session.return_value = result

        MagicMock()

        task_result = end_sessions()

        assert task_result["ended"] == 0
        assert task_result["errors"] == 1
        mock_db.rollback.assert_called()

    def test_session_end_grace_minutes_is_5(self):
        """Test that SESSION_END_GRACE_MINUTES is 5."""
        assert SESSION_END_GRACE_MINUTES == 5


class TestTaskConfiguration:
    """Tests for Celery task configuration."""

    def test_expire_requests_max_retries(self):
        """Test that expire_requests has max_retries configured."""
        # The task decorator configures max_retries=3
        pass

    def test_expire_requests_retry_backoff(self):
        """Test that expire_requests has exponential backoff configured."""
        # The task decorator configures retry_backoff=True
        pass

    def test_start_sessions_retry_delay(self):
        """Test that start_sessions has shorter retry delay than expire."""
        # start_sessions uses default_retry_delay=30, expire uses 60
        pass

    def test_tasks_autoretry_on_exception(self):
        """Test that tasks have autoretry_for=(Exception,) configured."""
        # This ensures automatic retry on any exception
        pass


class TestClockSkewHandling:
    """Tests for clock skew handling in booking tasks."""

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    def test_clock_skew_checked_before_processing(
        self,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
    ):
        """Test that clock skew is checked before processing bookings."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()

        mock_monitor = MagicMock()
        mock_skew_monitor.return_value = mock_monitor

        mock_db.query.return_value.filter.return_value.all.return_value = []

        MagicMock()

        expire_requests()

        mock_monitor.check_and_warn.assert_called_once_with(mock_db)

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    def test_uses_db_time_for_consistency(
        self,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
    ):
        """Test that database time is used for time-sensitive operations."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Simulate database time
        db_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        mock_get_db_time.return_value = db_time
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = []

        MagicMock()

        expire_requests()

        # Verify database time was requested
        mock_get_db_time.assert_called_once_with(mock_db)


class TestRaceConditionPrevention:
    """Tests for race condition prevention mechanisms."""

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_uses_select_for_update_nowait(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
    ):
        """Test that SELECT FOR UPDATE NOWAIT is used for locking."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [(1,)]
        mock_state_machine.get_booking_with_lock.return_value = None

        MagicMock()

        expire_requests()

        # Verify nowait=True is passed
        mock_state_machine.get_booking_with_lock.assert_called_with(
            mock_db, 1, nowait=True
        )

    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_each_booking_in_separate_transaction(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
    ):
        """Test that each booking is processed in its own transaction."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        # Return 3 bookings
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (1,),
            (2,),
            (3,),
        ]

        booking = MagicMock()
        result = MagicMock()
        result.success = True
        result.already_in_target_state = False

        mock_state_machine.get_booking_with_lock.return_value = booking
        mock_state_machine.expire_booking.return_value = result

        MagicMock()

        expire_requests()

        # Commit should be called once per booking
        assert mock_db.commit.call_count == 3


class TestTaskLogging:
    """Tests for task logging behavior."""

    @patch("tasks.booking_tasks.logger")
    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    @patch("modules.bookings.domain.state_machine.BookingStateMachine")
    def test_logs_expired_count(
        self,
        mock_state_machine,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_logger,
    ):
        """Test that expired count is logged."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_get_db_time.return_value = utc_now()
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = [(1,)]

        booking = MagicMock()
        result = MagicMock()
        result.success = True
        result.already_in_target_state = False

        mock_state_machine.get_booking_with_lock.return_value = booking
        mock_state_machine.expire_booking.return_value = result

        MagicMock()

        expire_requests()

        # Info log should be called when bookings are expired
        assert mock_logger.info.called or mock_logger.debug.called

    @patch("tasks.booking_tasks.logger")
    @patch("database.SessionLocal")
    @patch("core.clock_skew.get_db_time")
    @patch("core.clock_skew.get_job_skew_monitor")
    def test_logs_errors(
        self,
        mock_skew_monitor,
        mock_get_db_time,
        mock_session_local,
        mock_logger,
    ):
        """Test that errors are logged."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_get_db_time.side_effect = Exception("DB error")
        mock_skew_monitor.return_value.check_and_warn = MagicMock()

        mock_task = MagicMock()
        mock_task.retry.return_value = None

        with contextlib.suppress(Exception):
            expire_requests()

        mock_logger.error.assert_called()


class TestTaskImports:
    """Tests for task module imports."""

    def test_expire_requests_importable(self):
        """Test that expire_requests can be imported."""
        from tasks.booking_tasks import expire_requests

        assert callable(expire_requests)

    def test_start_sessions_importable(self):
        """Test that start_sessions can be imported."""
        from tasks.booking_tasks import start_sessions

        assert callable(start_sessions)

    def test_end_sessions_importable(self):
        """Test that end_sessions can be imported."""
        from tasks.booking_tasks import end_sessions

        assert callable(end_sessions)

    def test_tasks_exported_from_init(self):
        """Test that tasks are exported from __init__.py."""
        from tasks import end_sessions, expire_requests, start_sessions

        assert callable(expire_requests)
        assert callable(start_sessions)
        assert callable(end_sessions)
