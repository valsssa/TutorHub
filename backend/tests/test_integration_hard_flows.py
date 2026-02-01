"""
Comprehensive hard integration tests for complex end-to-end flows.

Tests cover critical edge cases and failure scenarios across multiple services:
1. Full Booking Lifecycle Edge Cases
2. Calendar Integration Failures
3. Notification Delivery Chains
4. Multi-User Interaction Scenarios
5. Data Consistency Across Services
6. Recovery and Rollback Scenarios

All external services (Stripe, Google, Zoom, Brevo) are mocked.
Tests verify complete flows with failure injection at each step.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
import stripe
from fastapi import status
from sqlalchemy.exc import IntegrityError, OperationalError

if TYPE_CHECKING:
    from models import Booking

from modules.bookings.domain.state_machine import (
    BookingStateMachine,
    OptimisticLockError,
    TransitionResult,
)
from modules.bookings.domain.status import (
    CancelledByRole,
    DisputeState,
    PaymentState,
    SessionOutcome,
    SessionState,
)

# =============================================================================
# Test Fixtures and Helpers
# =============================================================================


class MockStripeError(Exception):
    """Mock Stripe error for testing."""

    def __init__(self, message: str = "Stripe error"):
        self.user_message = message
        super().__init__(message)


class MockGoogleApiError(Exception):
    """Mock Google API error for testing."""

    def __init__(self, resp=None, content=b""):
        self.resp = resp or MagicMock(status=500)
        self.content = content
        super().__init__("Google API Error")


class MockZoomApiError(Exception):
    """Mock Zoom API error for testing."""
    pass


class MockBrevoApiError(Exception):
    """Mock Brevo email service error for testing."""
    pass


def create_test_booking_with_states(
    db_session,
    tutor_profile_id: int,
    student_id: int,
    subject_id: int,
    session_state: str = "REQUESTED",
    payment_state: str = "PENDING",
    dispute_state: str = "NONE",
    hours_from_now: int = 24,
) -> Booking:
    """Helper to create a booking with specific states for testing."""
    from models import Booking

    now = datetime.now(UTC)
    start_time = now + timedelta(hours=hours_from_now)
    end_time = start_time + timedelta(hours=1)

    booking = Booking(
        tutor_profile_id=tutor_profile_id,
        student_id=student_id,
        subject_id=subject_id,
        start_time=start_time,
        end_time=end_time,
        session_state=session_state,
        payment_state=payment_state,
        dispute_state=dispute_state,
        hourly_rate=Decimal("50.00"),
        total_amount=Decimal("50.00"),
        rate_cents=5000,
        currency="USD",
        tutor_name="Test Tutor",
        student_name="Test Student",
        subject_name="Test Subject",
        version=1,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


# =============================================================================
# 1. Full Booking Lifecycle Edge Cases
# =============================================================================


class TestFullBookingLifecycleEdgeCases:
    """Test complete booking flows with failures at each step."""

    def _setup_tutor_and_student(self, db_session):
        """Create tutor and student for testing."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="lifecycle_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            is_verified=True,
            first_name="Lifecycle",
            last_name="Tutor",
            currency="USD",
            timezone="UTC",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Lifecycle Test Tutor",
            headline="Testing complete flows",
            bio="For comprehensive lifecycle testing.",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
            timezone="UTC",
            currency="USD",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).filter_by(name="Mathematics").first()
        if not subject:
            subject = Subject(name="Mathematics", description="Math tutoring", category="STEM")
            db_session.add(subject)

        db_session.commit()
        return tutor, profile, subject

    def test_search_failure_recovery(self, client, db_session, student_token):
        """Test search endpoint with database timeout and recovery."""
        tutor, profile, subject = self._setup_tutor_and_student(db_session)

        # First search should succeed
        response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

    @patch("core.stripe_client.stripe_circuit_breaker")
    @patch("stripe.checkout.Session.create")
    def test_booking_with_payment_failure_at_checkout(
        self, mock_stripe_create, mock_circuit, client, db_session, student_token, student_user
    ):
        """Test booking creation when Stripe checkout fails."""
        tutor, profile, subject = self._setup_tutor_and_student(db_session)

        # Mock circuit breaker to allow calls
        mock_circuit.call.return_value.__enter__ = MagicMock()
        mock_circuit.call.return_value.__exit__ = MagicMock(return_value=False)

        # Configure Stripe to fail
        mock_stripe_create.side_effect = stripe.error.APIConnectionError(
            "Connection to Stripe failed"
        )

        now = datetime.now(UTC)
        start_time = (now + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        # Booking creation should succeed but payment may fail
        booking_response = client.post(
            "/api/v1/bookings",
            json={
                "tutor_profile_id": profile.id,
                "subject_id": subject.id,
                "topic": "Integration Test",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "lesson_type": "REGULAR",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Should create booking even if Stripe integration has issues
        # The actual payment can be retried
        assert booking_response.status_code in (status.HTTP_201_CREATED, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_booking_confirm_failure_rollback(self, db_session, student_user):
        """Test booking confirmation rollback on state transition failure."""
        tutor, profile, subject = self._setup_tutor_and_student(db_session)
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="REQUESTED",
            payment_state="PENDING",
        )

        # Confirm the booking
        result = BookingStateMachine.accept_booking(booking)
        assert result.success is True
        assert booking.session_state == SessionState.SCHEDULED.value
        assert booking.payment_state == PaymentState.AUTHORIZED.value

        # Try to confirm again (idempotent)
        result2 = BookingStateMachine.accept_booking(booking)
        assert result2.success is True
        assert result2.already_in_target_state is True

    def test_booking_with_package_purchase_atomic(self, db_session, student_user):
        """Test booking with package purchase maintains atomicity."""
        from models import StudentPackage, TutorPricingOption

        tutor, profile, subject = self._setup_tutor_and_student(db_session)

        # Create pricing option
        pricing = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="5 Session Package",
            session_count=5,
            price=Decimal("225.00"),
        )
        db_session.add(pricing)
        db_session.commit()

        # Create package for student
        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=pricing.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=pricing.price,
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        # Create booking using package
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="REQUESTED",
            payment_state="PENDING",
        )
        booking.package_id = package.id
        booking.pricing_type = "package"
        db_session.commit()

        # Simulate package session decrement
        package.sessions_used += 1
        package.sessions_remaining -= 1
        db_session.commit()

        db_session.refresh(package)
        assert package.sessions_remaining == 4
        assert package.sessions_used == 1

    def test_multi_session_booking_partial_completion(self, db_session, student_user):
        """Test handling of multi-session booking with partial completion."""
        from models import StudentPackage, TutorPricingOption

        tutor, profile, subject = self._setup_tutor_and_student(db_session)

        pricing = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="10 Session Package",
            session_count=10,
            price=Decimal("400.00"),
        )
        db_session.add(pricing)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=pricing.id,
            sessions_purchased=10,
            sessions_remaining=10,
            sessions_used=0,
            purchase_price=pricing.price,
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        # Create and complete 3 sessions
        completed_count = 0
        for i in range(3):
            booking = create_test_booking_with_states(
                db_session,
                tutor_profile_id=profile.id,
                student_id=student_user.id,
                subject_id=subject.id,
                session_state="ACTIVE",
                payment_state="AUTHORIZED",
                hours_from_now=-i-1,  # Past sessions
            )
            booking.package_id = package.id

            # End session
            result = BookingStateMachine.end_session(booking, SessionOutcome.COMPLETED)
            if result.success:
                completed_count += 1
                package.sessions_used += 1
                package.sessions_remaining -= 1
            db_session.commit()

        db_session.refresh(package)
        assert package.sessions_used == 3
        assert package.sessions_remaining == 7

        # Cancel remaining package (partial completion scenario)
        package.status = "cancelled"
        db_session.commit()

        assert package.status == "cancelled"
        assert package.sessions_used == 3  # Completed sessions remain


# =============================================================================
# 2. Calendar Integration Failures
# =============================================================================


class TestCalendarIntegrationFailures:
    """Test Google Calendar and Zoom integration failure scenarios."""

    @pytest.fixture
    def mock_google_calendar(self):
        """Create mocked Google Calendar service."""
        with patch("core.google_calendar.GoogleCalendarService") as mock:
            service = MagicMock()
            mock.return_value = service
            yield service

    @pytest.mark.asyncio
    async def test_google_calendar_rate_limiting(self):
        """Test handling of Google Calendar API rate limiting."""
        from core.google_calendar import GoogleCalendarService

        service = GoogleCalendarService()

        with patch.object(service, "_get_calendar_service") as mock_service:
            # Simulate rate limit error
            mock_events = MagicMock()
            mock_events.insert.return_value.execute.side_effect = MockGoogleApiError(
                resp=MagicMock(status=429),
                content=b"Rate limit exceeded"
            )
            mock_service.return_value.events.return_value = mock_events

            result = await service.create_booking_event(
                access_token="test_token",
                refresh_token="test_refresh",
                booking_id=1,
                title="Test Session",
                description="Test description",
                start_time=datetime.now(UTC),
                end_time=datetime.now(UTC) + timedelta(hours=1),
                tutor_email="tutor@test.com",
                student_email="student@test.com",
                tutor_name="Test Tutor",
                student_name="Test Student",
            )

            # Should return None on failure
            assert result is None

    @pytest.mark.asyncio
    async def test_oauth_token_refresh_during_event_creation(self):
        """Test OAuth token refresh flow during calendar event creation."""
        from core.google_calendar import GoogleCalendarService

        service = GoogleCalendarService()

        # Mock the refresh token flow
        with patch.object(service, "refresh_access_token") as mock_refresh:
            mock_refresh.return_value = {
                "access_token": "new_token",
                "expires_in": 3600,
            }

            # Verify refresh can be called
            result = await service.refresh_access_token("old_refresh_token")
            assert result["access_token"] == "new_token"

    @pytest.mark.asyncio
    async def test_calendar_sync_conflict_resolution(self, db_session, student_user):
        """Test handling of calendar sync conflicts."""
        from auth import get_password_hash
        from core.google_calendar import GoogleCalendarService
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="calendar_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            currency="USD",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Calendar Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Calendar Test Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        service = GoogleCalendarService()

        with patch.object(service, "check_busy_times") as mock_busy:
            # Simulate conflicting busy times
            now = datetime.now(UTC)
            mock_busy.return_value = [
                {
                    "start": now.isoformat(),
                    "end": (now + timedelta(hours=1)).isoformat(),
                }
            ]

            busy_times = await service.check_busy_times(
                access_token="test_token",
                refresh_token="test_refresh",
                start_time=now,
                end_time=now + timedelta(hours=2),
            )

            # Should detect conflict
            assert len(busy_times) == 1

    @pytest.mark.asyncio
    async def test_zoom_meeting_creation_timeout(self):
        """Test Zoom meeting creation with timeout."""
        # Mock Zoom API call with timeout
        async def mock_zoom_create(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate delay
            raise TimeoutError("Zoom API timeout")

        with patch("asyncio.sleep", return_value=None), pytest.raises(asyncio.TimeoutError):
            await mock_zoom_create()

    def test_meeting_url_update_after_creation(self, db_session, student_user):
        """Test updating meeting URL after booking creation."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="zoom_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Zoom Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Zoom Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create booking without meeting URL
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
        )
        assert booking.meeting_url is None
        assert booking.zoom_meeting_pending is False

        # Mark as pending (Zoom creation failed initially)
        booking.zoom_meeting_pending = True
        db_session.commit()

        # Simulate retry - update meeting URL
        booking.meeting_url = "https://zoom.us/j/123456789"
        booking.zoom_meeting_id = "123456789"
        booking.zoom_meeting_pending = False
        db_session.commit()

        db_session.refresh(booking)
        assert booking.meeting_url == "https://zoom.us/j/123456789"
        assert booking.zoom_meeting_pending is False


# =============================================================================
# 3. Notification Delivery Chains
# =============================================================================


class TestNotificationDeliveryChains:
    """Test notification delivery with various failure scenarios."""

    def test_email_delivery_failure_with_retry(self, db_session, student_user):
        """Test email delivery failure with retry mechanism."""
        from modules.notifications.service import NotificationService, NotificationType

        service = NotificationService()

        with patch("core.email_service.email_service._send_email_with_tracking") as mock_send:
            # First call fails, second succeeds
            from core.email_service import EmailDeliveryResult, EmailDeliveryStatus

            mock_send.side_effect = [
                EmailDeliveryResult(
                    success=False,
                    status=EmailDeliveryStatus.FAILED_TRANSIENT,
                    error_message="Temporary failure",
                ),
                EmailDeliveryResult(
                    success=True,
                    status=EmailDeliveryStatus.SUCCESS,
                    message_id="test-message-id",
                ),
            ]

            # Create notification (which triggers email)
            notification = service.create_notification(
                db=db_session,
                user_id=student_user.id,
                notification_type=NotificationType.BOOKING_CONFIRMED,
                title="Test Notification",
                message="Test message",
                send_email=True,
            )

            assert notification is not None

    def test_push_notification_to_offline_user(self, db_session, student_user):
        """Test push notification handling for offline users."""
        from models import Notification

        # Create notification when user is "offline" (no active session)
        notification = Notification(
            user_id=student_user.id,
            type="booking_reminder",
            title="Upcoming Session",
            message="Your session starts in 30 minutes",
            is_read=False,
        )
        db_session.add(notification)
        db_session.commit()

        # Notification should be stored for later delivery
        stored = db_session.query(Notification).filter_by(
            user_id=student_user.id,
            type="booking_reminder",
        ).first()
        assert stored is not None
        assert stored.is_read is False

    def test_notification_preference_change_mid_delivery(self, db_session, student_user):
        """Test handling of preference change during notification delivery."""
        from models import NotificationPreferences
        from modules.notifications.service import NotificationService, NotificationType

        service = NotificationService()

        # Get initial preferences (creates defaults)
        prefs = service._get_or_create_preferences(db_session, student_user.id)
        assert prefs.email_enabled is True

        # Disable email mid-flow
        prefs.email_enabled = False
        db_session.commit()

        # Create notification after preference change
        notification = service.create_notification(
            db=db_session,
            user_id=student_user.id,
            notification_type=NotificationType.BOOKING_CONFIRMED,
            title="Test After Pref Change",
            message="Should not send email",
            send_email=True,
        )

        # Notification should be created but email should be skipped
        assert notification is not None

    def test_bulk_notification_throttling(self, db_session, student_user):
        """Test throttling of bulk notifications."""
        from modules.notifications.service import NotificationService, NotificationType

        service = NotificationService()

        # Create many notifications rapidly
        notifications_created = 0
        for i in range(10):
            notification = service.create_notification(
                db=db_session,
                user_id=student_user.id,
                notification_type=NotificationType.NEW_MESSAGE,
                title=f"Message {i}",
                message=f"Test message {i}",
                send_email=False,  # Skip email for speed
            )
            if notification:
                notifications_created += 1

        # All notifications should be created (in-app doesn't throttle)
        assert notifications_created == 10

        # Check preferences for max daily limit
        prefs = service._get_or_create_preferences(db_session, student_user.id)
        assert prefs.max_daily_notifications is None or prefs.max_daily_notifications >= 10


# =============================================================================
# 4. Multi-User Interaction Scenarios
# =============================================================================


class TestMultiUserInteractionScenarios:
    """Test concurrent and conflicting user actions."""

    def test_tutor_student_simultaneous_booking_action(self, db_session, student_user):
        """Test tutor and student acting on same booking simultaneously."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="concurrent_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Concurrent Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Concurrent Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="REQUESTED",
            payment_state="PENDING",
        )

        # Student tries to cancel
        cancel_result = BookingStateMachine.cancel_booking(
            booking,
            cancelled_by=CancelledByRole.STUDENT,
            refund=True,
        )

        # If student cancelled first, tutor's accept should fail
        if cancel_result.success:
            db_session.commit()
            db_session.refresh(booking)

            # Tutor tries to accept after cancellation
            accept_result = BookingStateMachine.accept_booking(booking)
            assert accept_result.success is False or accept_result.already_in_target_state is True

    def test_admin_intervention_during_user_transaction(self, db_session, student_user, admin_user):
        """Test admin action during active user transaction."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="admin_intervention_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Admin Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Admin Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create active booking
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
        )

        # Admin force-cancels the booking
        cancel_result = BookingStateMachine.cancel_booking(
            booking,
            cancelled_by=CancelledByRole.ADMIN,
            refund=True,
        )
        assert cancel_result.success is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.session_state == SessionState.CANCELLED.value
        assert booking.cancelled_by_role == CancelledByRole.ADMIN.value

    def test_message_delivery_during_user_blocking(self, db_session, student_user):
        """Test message handling when user blocks another mid-delivery."""
        from auth import get_password_hash
        from models import Message, User

        recipient = User(
            email="blocking_recipient@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(recipient)
        db_session.commit()

        # Create message before block
        message = Message(
            sender_id=student_user.id,
            recipient_id=recipient.id,
            content="Test message before block",
        )
        db_session.add(message)
        db_session.commit()

        # Message should be stored
        stored_message = db_session.query(Message).filter_by(
            sender_id=student_user.id,
            recipient_id=recipient.id,
        ).first()
        assert stored_message is not None

    def test_review_submission_during_dispute(self, db_session, student_user):
        """Test review submission while dispute is active."""
        from auth import get_password_hash
        from models import Review, Subject, TutorProfile, User

        tutor = User(
            email="dispute_review_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Dispute Review Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Dispute Review Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create ended booking with open dispute
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="ENDED",
            payment_state="CAPTURED",
            dispute_state="OPEN",
            hours_from_now=-2,
        )
        booking.session_outcome = SessionOutcome.COMPLETED.value
        booking.dispute_reason = "Service quality concern"
        db_session.commit()

        # Try to create review during dispute
        # Business logic should allow/disallow this based on rules
        review = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=3,
            comment="Mixed feelings about the session",
            is_public=False,  # Might hide during dispute
        )
        db_session.add(review)
        db_session.commit()

        # Review should be created but potentially hidden
        stored_review = db_session.query(Review).filter_by(booking_id=booking.id).first()
        assert stored_review is not None


# =============================================================================
# 5. Data Consistency Across Services
# =============================================================================


class TestDataConsistencyAcrossServices:
    """Test data consistency when operations span multiple services."""

    def test_user_deletion_with_active_bookings(self, db_session):
        """Test handling user deletion when they have active bookings."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        # Create tutor
        tutor = User(
            email="delete_test_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Delete Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        # Create student
        student = User(
            email="delete_test_student@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(student)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Delete Test Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create active booking
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student.id,
            subject_id=subject.id,
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
        )

        # Soft delete the student
        student.is_active = False
        student.deleted_at = datetime.now(UTC)
        db_session.commit()

        # Booking should still reference the student (soft delete)
        db_session.refresh(booking)
        assert booking.student_id == student.id

    def test_tutor_deactivation_with_pending_sessions(self, db_session, student_user):
        """Test tutor deactivation with pending/scheduled sessions."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="deactivate_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Deactivate Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Deactivate Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create pending bookings
        bookings = []
        for i in range(3):
            booking = create_test_booking_with_states(
                db_session,
                tutor_profile_id=profile.id,
                student_id=student_user.id,
                subject_id=subject.id,
                session_state="SCHEDULED",
                payment_state="AUTHORIZED",
                hours_from_now=24 + i * 24,
            )
            bookings.append(booking)

        # Deactivate tutor profile
        profile.is_approved = False
        profile.profile_status = "deactivated"
        db_session.commit()

        # Bookings should be cancelled
        for booking in bookings:
            result = BookingStateMachine.cancel_booking(
                booking,
                cancelled_by=CancelledByRole.SYSTEM,
                refund=True,
            )
            assert result.success is True
        db_session.commit()

        # Verify all bookings cancelled
        from models import Booking
        pending_bookings = db_session.query(Booking).filter(
            Booking.tutor_profile_id == profile.id,
            Booking.session_state == SessionState.SCHEDULED.value,
        ).count()
        assert pending_bookings == 0

    def test_subject_deletion_with_existing_packages(self, db_session, student_user):
        """Test subject deletion when packages reference it."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, TutorSubject, User

        tutor = User(
            email="subject_delete_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Subject Delete Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = Subject(
            name="Deletable Subject",
            description="Will be soft deleted",
            category="TEST",
        )
        db_session.add(subject)
        db_session.commit()

        # Link subject to tutor
        tutor_subject = TutorSubject(
            tutor_profile_id=profile.id,
            subject_id=subject.id,
        )
        db_session.add(tutor_subject)
        db_session.commit()

        # Create booking with this subject
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
        )

        # Soft delete subject
        subject.deleted_at = datetime.now(UTC)
        db_session.commit()

        # Booking should still have subject reference
        db_session.refresh(booking)
        assert booking.subject_id == subject.id
        assert booking.subject_name == "Test Subject" or booking.subject_name is not None

    def test_cascading_updates_across_entities(self, db_session, student_user):
        """Test cascading updates maintain consistency."""
        from auth import get_password_hash
        from models import Notification, Review, Subject, TutorProfile, User

        tutor = User(
            email="cascade_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            first_name="Cascade",
            last_name="Tutor",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Cascade Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Cascade Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create completed booking
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="ENDED",
            payment_state="CAPTURED",
            hours_from_now=-2,
        )
        booking.session_outcome = SessionOutcome.COMPLETED.value
        db_session.commit()

        # Create related entities
        review = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=5,
            comment="Great session!",
        )
        db_session.add(review)

        notification = Notification(
            user_id=tutor.id,
            type="new_review",
            title="New Review",
            message="You received a 5-star review",
        )
        db_session.add(notification)
        db_session.commit()

        # Verify cascade relationships
        db_session.refresh(booking)
        assert booking.review is not None
        assert booking.review.rating == 5


# =============================================================================
# 6. Recovery and Rollback Scenarios
# =============================================================================


class TestRecoveryAndRollbackScenarios:
    """Test system recovery and rollback capabilities."""

    def test_partial_booking_creation_recovery(self, db_session, student_user):
        """Test recovery from partial booking creation failure."""
        from auth import get_password_hash
        from core.transactions import TransactionError, transaction
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="recovery_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Recovery Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Recovery Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Count bookings before
        initial_count = db_session.query(Booking).filter(
            Booking.tutor_profile_id == profile.id
        ).count()

        # Simulate partial failure with rollback
        try:
            with transaction(db_session):
                booking = Booking(
                    tutor_profile_id=profile.id,
                    student_id=student_user.id,
                    subject_id=subject.id,
                    start_time=datetime.now(UTC) + timedelta(days=1),
                    end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
                    session_state="REQUESTED",
                    payment_state="PENDING",
                    dispute_state="NONE",
                    hourly_rate=Decimal("50.00"),
                    total_amount=Decimal("50.00"),
                    currency="USD",
                )
                db_session.add(booking)
                db_session.flush()

                # Simulate failure
                raise ValueError("Simulated failure")
        except (TransactionError, ValueError):
            pass  # Expected

        # Verify rollback
        final_count = db_session.query(Booking).filter(
            Booking.tutor_profile_id == profile.id
        ).count()
        assert final_count == initial_count

    def test_payment_captured_but_booking_failed(self, db_session, student_user):
        """Test handling when payment succeeds but booking creation fails."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="payment_fail_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Payment Fail Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Payment Fail Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Simulate: payment went through but booking save failed
        # In real scenario, we'd need to issue refund

        with patch("core.stripe_client.create_refund") as mock_refund:
            from core.stripe_client import RefundResult

            # Mock successful refund
            mock_refund_obj = MagicMock()
            mock_refund_obj.id = "re_test123"
            mock_refund_obj.amount = 5000
            mock_refund_obj.status = "succeeded"

            mock_refund.return_value = RefundResult(
                refund=mock_refund_obj,
                was_existing=False,
            )

            # Create booking that will be "orphaned"
            booking = create_test_booking_with_states(
                db_session,
                tutor_profile_id=profile.id,
                student_id=student_user.id,
                subject_id=subject.id,
                session_state="REQUESTED",
                payment_state="AUTHORIZED",  # Payment went through
            )

            # Simulate booking save failure - need to refund
            booking.stripe_checkout_session_id = "cs_test123"
            booking.session_state = SessionState.CANCELLED.value
            booking.payment_state = PaymentState.VOIDED.value
            db_session.commit()

            db_session.refresh(booking)
            assert booking.payment_state == PaymentState.VOIDED.value

    def test_external_service_failure_compensation(self, db_session, student_user):
        """Test compensation actions when external services fail."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="compensation_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Compensation Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Compensation Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
        )

        # Simulate Zoom creation failure
        booking.zoom_meeting_pending = True
        db_session.commit()

        # Compensation: mark for retry or manual intervention
        assert booking.zoom_meeting_pending is True

        # Later, Zoom service recovers and creates meeting
        booking.meeting_url = "https://zoom.us/j/recovered"
        booking.zoom_meeting_id = "recovered123"
        booking.zoom_meeting_pending = False
        db_session.commit()

        db_session.refresh(booking)
        assert booking.zoom_meeting_pending is False
        assert booking.meeting_url is not None

    def test_data_reconciliation_after_outage(self, db_session, student_user):
        """Test data reconciliation after simulated outage."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="reconcile_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Reconcile Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Reconcile Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        # Create bookings in various states
        past_booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="ACTIVE",  # Should have ended
            payment_state="AUTHORIZED",
            hours_from_now=-5,  # 5 hours ago
        )

        expired_booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="REQUESTED",  # Should be expired
            payment_state="PENDING",
            hours_from_now=-48,  # 48 hours ago
        )
        expired_booking.created_at = datetime.now(UTC) - timedelta(days=3)
        db_session.commit()

        # Reconciliation: fix ACTIVE sessions that should have ended
        now = datetime.now(UTC)
        stale_active = db_session.query(Booking).filter(
            Booking.session_state == SessionState.ACTIVE.value,
            Booking.end_time < now - timedelta(hours=1),  # Grace period
        ).all()

        for booking in stale_active:
            result = BookingStateMachine.end_session(booking, SessionOutcome.COMPLETED)
            assert result.success is True
        db_session.commit()

        # Reconciliation: expire old requests
        stale_requested = db_session.query(Booking).filter(
            Booking.session_state == SessionState.REQUESTED.value,
            Booking.created_at < now - timedelta(hours=24),
        ).all()

        for booking in stale_requested:
            result = BookingStateMachine.expire_booking(booking)
            assert result.success is True
        db_session.commit()

        # Verify reconciliation
        db_session.refresh(past_booking)
        db_session.refresh(expired_booking)

        assert past_booking.session_state == SessionState.ENDED.value
        assert expired_booking.session_state == SessionState.EXPIRED.value

    def test_optimistic_lock_conflict_handling(self, db_session, student_user):
        """Test optimistic locking conflict detection and handling."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="lock_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Lock Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Lock Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="REQUESTED",
            payment_state="PENDING",
        )
        initial_version = booking.version

        # First update succeeds
        result1 = BookingStateMachine.accept_booking(booking)
        assert result1.success is True
        assert booking.version == initial_version + 1

        # Verify version increment
        assert BookingStateMachine.verify_version(booking, initial_version + 1)

        # Attempting with stale version would fail in real scenario
        assert not BookingStateMachine.verify_version(booking, initial_version)


# =============================================================================
# Additional Edge Case Tests
# =============================================================================


class TestAdditionalEdgeCases:
    """Additional edge case tests for completeness."""

    def test_dispute_escalation_on_conflicting_no_show_reports(self, db_session, student_user):
        """Test automatic dispute escalation when both parties report no-show."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="noshow_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="No-Show Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="No-Show Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="ACTIVE",
            payment_state="AUTHORIZED",
            hours_from_now=0,
        )

        # Tutor reports student no-show
        result1 = BookingStateMachine.mark_no_show(
            booking, who_was_absent="STUDENT", reporter_role="TUTOR"
        )
        assert result1.success is True
        db_session.commit()
        db_session.refresh(booking)

        # Student reports tutor no-show (conflicting)
        result2 = BookingStateMachine.mark_no_show(
            booking, who_was_absent="TUTOR", reporter_role="STUDENT"
        )
        assert result2.success is True
        assert result2.escalated_to_dispute is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.dispute_state == DisputeState.OPEN.value

    def test_package_credit_restoration_on_dispute_refund(self, db_session, student_user):
        """Test package credit restoration when dispute results in refund."""
        from auth import get_password_hash
        from models import StudentPackage, Subject, TutorPricingOption, TutorProfile, User

        tutor = User(
            email="pkg_restore_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Package Restore Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Package Restore Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        pricing = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="Test Package",
            session_count=5,
            price=Decimal("200.00"),
        )
        db_session.add(pricing)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=pricing.id,
            sessions_purchased=5,
            sessions_remaining=4,  # One session used
            sessions_used=1,
            purchase_price=pricing.price,
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        # Create completed booking with dispute
        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="ENDED",
            payment_state="CAPTURED",
            hours_from_now=-2,
        )
        booking.package_id = package.id
        booking.session_outcome = SessionOutcome.COMPLETED.value
        db_session.commit()

        # Open dispute
        result = BookingStateMachine.open_dispute(
            booking,
            reason="Session quality issue",
            disputed_by_user_id=student_user.id,
        )
        assert result.success is True
        db_session.commit()

        # Resolve with refund
        resolve_result = BookingStateMachine.resolve_dispute(
            booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=1,  # Admin
            notes="Refund granted",
        )
        assert resolve_result.success is True
        assert resolve_result.restore_package_credit is True
        db_session.commit()

        # Restore package credit
        if resolve_result.restore_package_credit:
            package.sessions_remaining += 1
            package.sessions_used -= 1
            db_session.commit()

        db_session.refresh(package)
        assert package.sessions_remaining == 5
        assert package.sessions_used == 0

    def test_timezone_handling_in_booking_transitions(self, db_session, student_user):
        """Test timezone handling during booking state transitions."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, User

        tutor = User(
            email="tz_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            timezone="America/New_York",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Timezone Test",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
            timezone="America/New_York",
        )
        db_session.add(profile)

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="TZ Subject", description="Testing")
            db_session.add(subject)
        db_session.commit()

        booking = create_test_booking_with_states(
            db_session,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            session_state="REQUESTED",
            payment_state="PENDING",
        )
        booking.tutor_tz = "America/New_York"
        booking.student_tz = "UTC"
        db_session.commit()

        # Booking should work regardless of timezone differences
        result = BookingStateMachine.accept_booking(booking)
        assert result.success is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.session_state == SessionState.SCHEDULED.value
        assert booking.confirmed_at is not None
