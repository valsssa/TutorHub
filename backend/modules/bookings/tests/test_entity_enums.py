"""Tests to verify booking entity uses valid enum values."""

from datetime import UTC, datetime, timezone

from core.datetime_utils import utc_now

from modules.bookings.domain.entities import BookingEntity
from modules.bookings.domain.status import SessionOutcome, SessionState


def test_booking_entity_default_session_state_is_valid():
    """Default session_state must be REQUESTED."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_id=1,
        tutor_profile_id=1,
        start_time=utc_now(),
        end_time=utc_now(),
    )
    assert entity.session_state == SessionState.REQUESTED


def test_booking_entity_default_session_outcome_is_none():
    """Default session_outcome should be None."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_id=1,
        tutor_profile_id=1,
        start_time=utc_now(),
        end_time=utc_now(),
    )
    assert entity.session_outcome is None


def test_is_confirmed_uses_scheduled_state():
    """is_confirmed property should check SCHEDULED state."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_id=1,
        tutor_profile_id=1,
        start_time=utc_now(),
        end_time=utc_now(),
        session_state=SessionState.SCHEDULED,
    )
    assert entity.is_confirmed is True


def test_is_completed_uses_ended_with_completed_outcome():
    """is_completed should check ENDED state with COMPLETED outcome."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_id=1,
        tutor_profile_id=1,
        start_time=utc_now(),
        end_time=utc_now(),
        session_state=SessionState.ENDED,
        session_outcome=SessionOutcome.COMPLETED,
    )
    assert entity.is_completed is True


def test_is_cancelled_uses_cancelled_state():
    """is_cancelled should check CANCELLED state."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_id=1,
        tutor_profile_id=1,
        start_time=utc_now(),
        end_time=utc_now(),
        session_state=SessionState.CANCELLED,
    )
    assert entity.is_cancelled is True


def test_can_start_uses_scheduled_state():
    """can_start should check SCHEDULED state."""
    past_time = datetime(2020, 1, 1, tzinfo=UTC)
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_id=1,
        tutor_profile_id=1,
        start_time=past_time,
        end_time=past_time,
        session_state=SessionState.SCHEDULED,
    )
    assert entity.can_start is True
