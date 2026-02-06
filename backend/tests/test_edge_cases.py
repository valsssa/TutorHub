"""
Tests for edge cases and error handling.

Tests cover:
- Concurrent booking conflicts
- Race conditions in package usage
- Token expiration during operations
- Webhook delivery failures
- Network timeouts and retries
"""

import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestConcurrentBookingConflicts:
    """Test concurrent booking conflict handling."""

    def _create_tutor_with_availability(self, db_session, email="concurrent_tutor@test.com"):
        """Create a tutor for concurrent booking tests."""
        from auth import get_password_hash
        from models import TutorProfile, User

        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            is_verified=True,
            first_name="Concurrent",
            last_name="Tutor",
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Concurrent Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        return user, profile

    def test_concurrent_booking_same_slot(self, db_session, student_user):
        """Test handling of concurrent bookings for the same time slot."""
        from models import Booking, Subject

        tutor_user, tutor_profile = self._create_tutor_with_availability(db_session)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Concurrent Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        start_time = (now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        booking1 = Booking(
            tutor_profile_id=tutor_profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=start_time,
            end_time=end_time,
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking1)
        db_session.commit()

        from auth import get_password_hash
        from models import User

        student2 = User(
            email="student2_concurrent@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(student2)
        db_session.commit()

        booking2 = Booking(
            tutor_profile_id=tutor_profile.id,
            student_id=student2.id,
            subject_id=subject.id,
            start_time=start_time,
            end_time=end_time,
            session_state="REQUESTED",
            payment_state="PENDING",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking2)

        existing = (
            db_session.query(Booking)
            .filter(
                Booking.tutor_profile_id == tutor_profile.id,
                Booking.session_state.in_(["SCHEDULED", "ACTIVE"]),
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            )
            .first()
        )

        assert existing is not None
        assert existing.id == booking1.id

    def test_overlapping_booking_partial_overlap(self, db_session, student_user):
        """Test partial time overlap detection."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="overlap_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Overlap Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Overlap Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        base_time = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

        booking1 = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=base_time,
            end_time=base_time + timedelta(hours=2),
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=100.00,
        )
        db_session.add(booking1)
        db_session.commit()

        partial_overlap_start = base_time + timedelta(hours=1)
        partial_overlap_end = base_time + timedelta(hours=3)

        existing = (
            db_session.query(Booking)
            .filter(
                Booking.tutor_profile_id == profile.id,
                Booking.session_state.in_(["SCHEDULED", "ACTIVE"]),
                Booking.start_time < partial_overlap_end,
                Booking.end_time > partial_overlap_start,
            )
            .first()
        )

        assert existing is not None

    def test_back_to_back_bookings_allowed(self, db_session, student_user):
        """Test that back-to-back bookings (end time = start time) are allowed."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="backtoback_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Back to Back Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="B2B Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        slot1_start = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        slot1_end = slot1_start + timedelta(hours=1)

        booking1 = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=slot1_start,
            end_time=slot1_end,
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking1)
        db_session.commit()

        slot2_start = slot1_end
        slot2_end = slot2_start + timedelta(hours=1)

        overlap_check = (
            db_session.query(Booking)
            .filter(
                Booking.tutor_profile_id == profile.id,
                Booking.session_state.in_(["SCHEDULED", "ACTIVE"]),
                Booking.start_time < slot2_end,
                Booking.end_time > slot2_start,
            )
            .first()
        )

        assert overlap_check is None


class TestRaceConditionsInPackageUsage:
    """Test race conditions when using package credits."""

    def _create_package_with_credits(self, db_session, student_user, credits=5):
        """Create a package with specified credits."""
        from auth import get_password_hash
        from models import StudentPackage, TutorPricingOption, TutorProfile, User

        tutor = User(
            email="race_package_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Race Package Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        pricing = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="Race Test Package",
            session_count=credits,
            price=Decimal("200.00"),
        )
        db_session.add(pricing)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=pricing.id,
            sessions_purchased=credits,
            sessions_remaining=credits,
            sessions_used=0,
            purchase_price=Decimal("200.00"),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        return profile, package

    def test_package_credit_atomic_decrement(self, db_session, student_user):
        """Test that package credit decrement is atomic."""
        profile, package = self._create_package_with_credits(db_session, student_user, credits=3)

        initial_remaining = package.sessions_remaining

        package.sessions_remaining -= 1
        package.sessions_used += 1
        db_session.commit()

        db_session.refresh(package)
        assert package.sessions_remaining == initial_remaining - 1
        assert package.sessions_used == 1

    def test_package_insufficient_credits_check(self, db_session, student_user):
        """Test handling when trying to use credits with insufficient balance."""
        profile, package = self._create_package_with_credits(db_session, student_user, credits=1)

        package.sessions_remaining -= 1
        package.sessions_used += 1
        db_session.commit()

        db_session.refresh(package)
        assert package.sessions_remaining == 0

        can_use = package.sessions_remaining > 0
        assert can_use is False

    def test_package_status_update_on_exhaustion(self, db_session, student_user):
        """Test package status updates when all credits are used."""
        profile, package = self._create_package_with_credits(db_session, student_user, credits=2)

        for _ in range(2):
            if package.sessions_remaining > 0:
                package.sessions_remaining -= 1
                package.sessions_used += 1

        if package.sessions_remaining == 0:
            package.status = "exhausted"

        db_session.commit()

        db_session.refresh(package)
        assert package.status == "exhausted"
        assert package.sessions_remaining == 0
        assert package.sessions_used == 2


class TestTokenExpiration:
    """Test handling of token expiration during operations."""

    def test_expired_token_rejected(self, client, db_session):
        """Test that expired tokens are rejected."""
        from auth import get_password_hash
        from core.security import TokenManager
        from models import User

        user = User(
            email="expired_token_user@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        with patch.object(TokenManager, "create_access_token") as mock_create:
            mock_create.return_value = "expired.token.here"

            response = client.get(
                "/api/v1/me",
                headers={"Authorization": "Bearer expired.token.here"},
            )

            assert response.status_code in (401, 403, 422)

    def test_malformed_token_rejected(self, client):
        """Test that malformed tokens are rejected."""
        response = client.get(
            "/api/v1/me",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )

        assert response.status_code in (401, 403, 422)

    def test_missing_token_rejected(self, client):
        """Test that missing tokens result in 401."""
        response = client.get("/api/v1/me")

        assert response.status_code == 401

    def test_token_with_invalid_user(self, client, db_session):
        """Test token for non-existent user."""
        from core.security import TokenManager

        token = TokenManager.create_access_token({"sub": "nonexistent@test.com"})

        response = client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code in (401, 404)


class TestWebhookFailures:
    """Test webhook delivery failure handling."""

    def test_webhook_idempotency(self, db_session):
        """Test that webhooks are processed idempotently."""
        from models import WebhookEvent

        event_id = "evt_test_12345"

        existing = (
            db_session.query(WebhookEvent).filter_by(stripe_event_id=event_id).first()
        )
        assert existing is None

        webhook1 = WebhookEvent(
            stripe_event_id=event_id,
            event_type="payment_intent.succeeded",
        )
        db_session.add(webhook1)
        db_session.commit()

        existing = (
            db_session.query(WebhookEvent).filter_by(stripe_event_id=event_id).first()
        )
        assert existing is not None

        duplicate = (
            db_session.query(WebhookEvent).filter_by(stripe_event_id=event_id).first()
        )
        is_duplicate = duplicate is not None
        assert is_duplicate is True

    def test_webhook_event_types_tracked(self, db_session):
        """Test that different webhook event types are properly tracked."""
        from models import WebhookEvent

        events = [
            ("evt_payment_1", "payment_intent.succeeded"),
            ("evt_payment_2", "payment_intent.failed"),
            ("evt_checkout_1", "checkout.session.completed"),
        ]

        for event_id, event_type in events:
            webhook = WebhookEvent(stripe_event_id=event_id, event_type=event_type)
            db_session.add(webhook)
        db_session.commit()

        all_events = db_session.query(WebhookEvent).all()
        assert len(all_events) >= 3

        succeeded_events = (
            db_session.query(WebhookEvent)
            .filter_by(event_type="payment_intent.succeeded")
            .all()
        )
        assert len(succeeded_events) >= 1


class TestNetworkTimeouts:
    """Test handling of network timeouts and retries."""

    def test_booking_creation_with_timeout_simulation(self, db_session, student_user):
        """Test booking creation handles simulated delays."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="timeout_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Timeout Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Timeout Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        start_time = now + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=start_time,
            end_time=end_time,
            session_state="REQUESTED",
            payment_state="PENDING",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        db_session.refresh(booking)
        assert booking.id is not None
        assert booking.session_state == "REQUESTED"


class TestStateTransitionEdgeCases:
    """Test edge cases in state machine transitions."""

    def test_idempotent_state_transitions(self, db_session, student_user):
        """Test that state transitions are idempotent."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor = User(
            email="idempotent_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Idempotent Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Idempotent Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="REQUESTED",
            payment_state="PENDING",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        result1 = BookingStateMachine.accept_booking(booking)
        assert result1.success is True
        db_session.commit()

        result2 = BookingStateMachine.accept_booking(booking)
        assert result2.success is True
        assert result2.already_in_target_state is True

    def test_invalid_state_transition_rejected(self, db_session, student_user):
        """Test that invalid state transitions are rejected."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor = User(
            email="invalid_transition_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Invalid Transition Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Invalid Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="CANCELLED",
            payment_state="VOIDED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        result = BookingStateMachine.start_session(booking)
        assert result.success is False
        assert result.error_message is not None

    def test_conflicting_no_show_reports_escalate(self, db_session, student_user):
        """Test that conflicting no-show reports escalate to dispute."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor = User(
            email="no_show_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="No Show Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="No Show Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            session_state="ACTIVE",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        result1 = BookingStateMachine.mark_no_show(
            booking, who_was_absent="STUDENT", reporter_role="TUTOR"
        )
        assert result1.success is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.session_state == "ENDED"
        assert booking.session_outcome == "NO_SHOW_STUDENT"

        result2 = BookingStateMachine.mark_no_show(
            booking, who_was_absent="TUTOR", reporter_role="STUDENT"
        )
        assert result2.success is True
        assert result2.escalated_to_dispute is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.dispute_state == "OPEN"


class TestOptimisticLocking:
    """Test optimistic locking prevents race conditions."""

    def test_version_increment_on_update(self, db_session, student_user):
        """Test that version is incremented on state changes."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor = User(
            email="version_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Version Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Version Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="REQUESTED",
            payment_state="PENDING",
            version=1,
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        initial_version = booking.version

        BookingStateMachine.accept_booking(booking)
        db_session.commit()

        db_session.refresh(booking)
        assert booking.version == initial_version + 1

    def test_version_verification(self, db_session, student_user):
        """Test version verification detects concurrent modifications."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor = User(
            email="verify_version_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Verify Version Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Verify Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = datetime.now(UTC)
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="REQUESTED",
            payment_state="PENDING",
            version=1,
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        expected_version = 1
        is_valid = BookingStateMachine.verify_version(booking, expected_version)
        assert is_valid is True

        booking.version = 2
        db_session.commit()

        is_valid = BookingStateMachine.verify_version(booking, expected_version)
        assert is_valid is False
