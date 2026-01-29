"""
Tests for booking policy engine.
Tests cancellation, reschedule, and no-show policies.
"""

from datetime import datetime

import pytest

from modules.bookings.policy_engine import (
    CancellationPolicy,
    GraceEditPolicy,
    NoShowPolicy,
    ReschedulePolicy,
)


class TestCancellationPolicy:
    """Test cancellation rules and refund logic."""

    def test_student_cancel_outside_window_full_refund(self):
        """Student cancels >= 12h before: full refund."""
        now = datetime(2025, 10, 20, 12, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)  # 24h away

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="REGULAR",
            is_trial=False,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"
        assert decision.refund_cents == 5000
        assert decision.restore_package_unit is False

    def test_student_cancel_inside_window_no_refund(self):
        """Student cancels < 24h before: no refund."""
        now = datetime(2025, 10, 21, 6, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)  # 6h away

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="REGULAR",
            is_trial=False,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "LATE_CANCEL"
        assert decision.refund_cents == 0

    def test_student_cancel_within_grace_period_full_refund(self):
        """Student cancels at 23h55m before (within 5-min grace): full refund."""
        # Booking starts at 12:00 on Oct 21
        # Cancelling at 12:05 on Oct 20 = 23h55m before start
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 20, 12, 5, 0)  # 23h55m before

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="REGULAR",
            is_trial=False,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"
        assert decision.refund_cents == 5000

    def test_student_cancel_just_outside_grace_no_refund(self):
        """Student cancels at 23h54m before (outside 5-min grace): no refund."""
        # Booking starts at 12:00 on Oct 21
        # Cancelling at 12:06 on Oct 20 = 23h54m before start
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 20, 12, 6, 0)  # 23h54m before

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="REGULAR",
            is_trial=False,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "LATE_CANCEL"
        assert decision.refund_cents == 0

    def test_student_cancel_at_exact_boundary_full_refund(self):
        """Student cancels at exactly 24h before: full refund."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 20, 12, 0, 0)  # Exactly 24h before

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="REGULAR",
            is_trial=False,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"
        assert decision.refund_cents == 5000

    def test_student_cancel_already_started(self):
        """Cannot cancel session that already started."""
        now = datetime(2025, 10, 21, 12, 30, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)  # 30 min ago

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="REGULAR",
            is_trial=False,
            is_package=False,
        )

        assert decision.allow is False
        assert decision.reason_code == "ALREADY_STARTED"

    def test_student_cancel_package_restores_credit(self):
        """Package lesson cancelled >= 12h: restores credit."""
        now = datetime(2025, 10, 20, 12, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)

        decision = CancellationPolicy.evaluate_student_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            lesson_type="PACKAGE",
            is_trial=False,
            is_package=True,
        )

        assert decision.allow is True
        assert decision.refund_cents == 0  # Package doesn't refund money
        assert decision.restore_package_unit is True

    def test_tutor_cancel_outside_window_no_penalty(self):
        """Tutor cancels >= 12h before: no penalty."""
        now = datetime(2025, 10, 20, 12, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)

        decision = CancellationPolicy.evaluate_tutor_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"
        assert decision.refund_cents == 5000
        assert decision.tutor_compensation_cents == 0
        assert decision.apply_strike_to_tutor is False

    def test_tutor_cancel_inside_window_with_penalty(self):
        """Tutor cancels < 24h before: penalty and compensation."""
        now = datetime(2025, 10, 21, 6, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)

        decision = CancellationPolicy.evaluate_tutor_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "TUTOR_LATE_CANCEL"
        assert decision.refund_cents == 5000
        assert decision.tutor_compensation_cents == 500  # $5 compensation
        assert decision.apply_strike_to_tutor is True

    def test_tutor_cancel_within_grace_period_no_penalty(self):
        """Tutor cancels at 23h55m before (within 5-min grace): no penalty."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 20, 12, 5, 0)  # 23h55m before

        decision = CancellationPolicy.evaluate_tutor_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"
        assert decision.refund_cents == 5000
        assert decision.tutor_compensation_cents == 0
        assert decision.apply_strike_to_tutor is False

    def test_tutor_cancel_just_outside_grace_with_penalty(self):
        """Tutor cancels at 23h54m before (outside 5-min grace): penalty."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 20, 12, 6, 0)  # 23h54m before

        decision = CancellationPolicy.evaluate_tutor_cancellation(
            booking_start_at=booking_start,
            now=now,
            rate_cents=5000,
            is_package=False,
        )

        assert decision.allow is True
        assert decision.reason_code == "TUTOR_LATE_CANCEL"
        assert decision.refund_cents == 5000
        assert decision.tutor_compensation_cents == 500
        assert decision.apply_strike_to_tutor is True


class TestReschedulePolicy:
    """Test rescheduling rules."""

    def test_reschedule_outside_window_allowed(self):
        """Reschedule >= 12h before: allowed."""
        now = datetime(2025, 10, 20, 12, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        new_start = datetime(2025, 10, 22, 14, 0, 0)

        decision = ReschedulePolicy.evaluate_reschedule(
            booking_start_at=booking_start,
            now=now,
            new_start_at=new_start,
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"

    def test_reschedule_inside_window_denied(self):
        """Reschedule < 12h before: denied."""
        now = datetime(2025, 10, 21, 6, 0, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        new_start = datetime(2025, 10, 22, 14, 0, 0)

        decision = ReschedulePolicy.evaluate_reschedule(
            booking_start_at=booking_start,
            now=now,
            new_start_at=new_start,
        )

        assert decision.allow is False
        assert decision.reason_code == "WINDOW_EXPIRED"

    def test_reschedule_already_started_denied(self):
        """Cannot reschedule session that already started."""
        now = datetime(2025, 10, 21, 12, 30, 0)
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        new_start = datetime(2025, 10, 22, 14, 0, 0)

        decision = ReschedulePolicy.evaluate_reschedule(
            booking_start_at=booking_start,
            now=now,
            new_start_at=new_start,
        )

        assert decision.allow is False
        assert decision.reason_code == "ALREADY_STARTED"

    def test_reschedule_past_time_denied(self):
        """Cannot reschedule to a time in the past."""
        now = datetime(2025, 10, 21, 12, 0, 0)
        booking_start = datetime(2025, 10, 22, 12, 0, 0)
        new_start = datetime(2025, 10, 20, 14, 0, 0)  # Past

        decision = ReschedulePolicy.evaluate_reschedule(
            booking_start_at=booking_start,
            now=now,
            new_start_at=new_start,
        )

        assert decision.allow is False
        assert decision.reason_code == "INVALID_NEW_TIME"


class TestNoShowPolicy:
    """Test no-show detection and reporting rules."""

    def test_mark_no_show_after_grace_period_allowed(self):
        """Can mark no-show after 10min grace period."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 21, 12, 15, 0)  # 15 min after

        decision = NoShowPolicy.evaluate_no_show_report(
            booking_start_at=booking_start,
            now=now,
            reporter_role="TUTOR",
        )

        assert decision.allow is True
        assert decision.reason_code == "OK"

    def test_mark_no_show_within_grace_period_denied(self):
        """Cannot mark no-show within 10min grace period."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 21, 12, 5, 0)  # Only 5 min

        decision = NoShowPolicy.evaluate_no_show_report(
            booking_start_at=booking_start,
            now=now,
            reporter_role="TUTOR",
        )

        assert decision.allow is False
        assert decision.reason_code == "GRACE_PERIOD"

    def test_mark_no_show_after_24h_denied(self):
        """Cannot report no-show after 24h window."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 22, 13, 0, 0)  # 25h later

        decision = NoShowPolicy.evaluate_no_show_report(
            booking_start_at=booking_start,
            now=now,
            reporter_role="TUTOR",
        )

        assert decision.allow is False
        assert decision.reason_code == "REPORT_WINDOW_EXPIRED"

    def test_student_reports_tutor_no_show_applies_strike(self):
        """Student reporting tutor no-show applies penalty."""
        booking_start = datetime(2025, 10, 21, 12, 0, 0)
        now = datetime(2025, 10, 21, 12, 15, 0)

        decision = NoShowPolicy.evaluate_no_show_report(
            booking_start_at=booking_start,
            now=now,
            reporter_role="STUDENT",
        )

        assert decision.allow is True
        assert decision.apply_strike_to_tutor is True


class TestGraceEditPolicy:
    """Test grace period edit rules."""

    def test_can_edit_within_grace_and_advance_booking(self):
        """Can edit within 5min if session is 24h+ away."""
        booking_created = datetime(2025, 10, 20, 12, 0, 0)
        booking_start = datetime(2025, 10, 22, 12, 0, 0)  # 48h away
        now = datetime(2025, 10, 20, 12, 3, 0)  # 3 min after creation

        can_edit = GraceEditPolicy.can_edit_in_grace(
            booking_created_at=booking_created,
            booking_start_at=booking_start,
            now=now,
        )

        assert can_edit is True

    def test_cannot_edit_after_grace_period(self):
        """Cannot edit after 5min grace period."""
        booking_created = datetime(2025, 10, 20, 12, 0, 0)
        booking_start = datetime(2025, 10, 22, 12, 0, 0)
        now = datetime(2025, 10, 20, 12, 10, 0)  # 10 min after

        can_edit = GraceEditPolicy.can_edit_in_grace(
            booking_created_at=booking_created,
            booking_start_at=booking_start,
            now=now,
        )

        assert can_edit is False

    def test_cannot_edit_if_too_close_to_start(self):
        """Cannot edit in grace if session < 24h away."""
        booking_created = datetime(2025, 10, 21, 12, 0, 0)
        booking_start = datetime(2025, 10, 21, 18, 0, 0)  # 6h away
        now = datetime(2025, 10, 21, 12, 2, 0)  # Within grace

        can_edit = GraceEditPolicy.can_edit_in_grace(
            booking_created_at=booking_created,
            booking_start_at=booking_start,
            now=now,
        )

        assert can_edit is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
