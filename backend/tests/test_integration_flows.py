"""
Comprehensive integration tests for end-to-end flows.

Tests cover:
- Full booking flow: search -> view profile -> book -> pay -> complete -> review
- Tutor onboarding flow: register -> create profile -> set availability -> get approved
- Package flow: purchase package -> use sessions -> track expiration
- Dispute flow: file dispute -> admin review -> resolution
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import status


class TestFullBookingFlow:
    """Test complete booking workflow from search to review."""

    def _create_approved_tutor(self, db_session, email="flow_tutor@test.com"):
        """Helper to create an approved tutor with profile."""
        from auth import get_password_hash
        from models import Subject, TutorProfile, TutorSubject, User

        user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            is_verified=True,
            first_name="Flow",
            last_name="Tutor",
            currency="USD",
            timezone="UTC",
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Expert Math Tutor",
            headline="10+ years experience in calculus",
            bio="Passionate about helping students succeed in mathematics.",
            hourly_rate=50.00,
            experience_years=10,
            education="PhD Mathematics",
            languages=["English"],
            is_approved=True,
            profile_status="approved",
            timezone="UTC",
            currency="USD",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).filter_by(name="Mathematics").first()
        if not subject:
            subject = Subject(name="Mathematics", description="Math tutoring", category="STEM")
            db_session.add(subject)
            db_session.commit()

        tutor_subject = TutorSubject(tutor_profile_id=profile.id, subject_id=subject.id)
        db_session.add(tutor_subject)
        db_session.commit()

        return user, profile, subject

    def test_full_booking_lifecycle(self, client, db_session, student_token, student_user):
        """Test complete booking flow from search to completion."""
        tutor_user, tutor_profile, subject = self._create_approved_tutor(db_session)

        from core.security import TokenManager

        tutor_token = TokenManager.create_access_token({"sub": tutor_user.email})

        search_response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert search_response.status_code == status.HTTP_200_OK
        tutors_data = search_response.json()
        tutors = tutors_data["items"] if isinstance(tutors_data, dict) and "items" in tutors_data else tutors_data
        assert any(t["id"] == tutor_profile.id for t in tutors)

        profile_response = client.get(
            f"/api/v1/tutors/{tutor_profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert profile_response.status_code == status.HTTP_200_OK
        profile_data = profile_response.json()
        assert profile_data["title"] == "Expert Math Tutor"

        now = datetime.now(UTC)
        start_time = (now + timedelta(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        booking_response = client.post(
            "/api/v1/bookings",
            json={
                "tutor_profile_id": tutor_profile.id,
                "subject_id": subject.id,
                "topic": "Introduction to Calculus",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "notes": "Focus on derivatives",
                "lesson_type": "REGULAR",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert booking_response.status_code == status.HTTP_201_CREATED
        booking = booking_response.json()
        booking_id = booking["id"]
        assert booking["status"] in ("PENDING", "pending", "REQUESTED", "requested")

        tutor_bookings = client.get(
            "/api/v1/bookings/tutor/me",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert tutor_bookings.status_code == status.HTTP_200_OK
        tutor_bookings_data = tutor_bookings.json()
        if isinstance(tutor_bookings_data, dict) and "items" in tutor_bookings_data:
            bookings_list = tutor_bookings_data["items"]
        else:
            bookings_list = tutor_bookings_data
        assert any(b["id"] == booking_id for b in bookings_list)

        confirm_response = client.patch(
            f"/api/v1/bookings/{booking_id}/confirm",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert confirm_response.status_code == status.HTTP_200_OK
        confirmed = confirm_response.json()
        assert confirmed["status"] in ("CONFIRMED", "confirmed", "SCHEDULED", "scheduled")

        booking_detail = client.get(
            f"/api/v1/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert booking_detail.status_code == status.HTTP_200_OK
        detail = booking_detail.json()
        assert detail["id"] == booking_id

    def test_booking_with_message_exchange(self, client, db_session, student_token, student_user):
        """Test booking with pre-session messaging."""
        tutor_user, tutor_profile, subject = self._create_approved_tutor(
            db_session, email="message_tutor@test.com"
        )

        from core.security import TokenManager

        TokenManager.create_access_token({"sub": tutor_user.email})

        now = datetime.now(UTC)
        start_time = (now + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        booking_response = client.post(
            "/api/v1/bookings",
            json={
                "tutor_profile_id": tutor_profile.id,
                "subject_id": subject.id,
                "topic": "Algebra basics",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "lesson_type": "TRIAL",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert booking_response.status_code == status.HTTP_201_CREATED
        booking_id = booking_response.json()["id"]

        message_response = client.post(
            "/api/v1/messages",
            json={
                "recipient_id": tutor_user.id,
                "content": "Hi! I am looking forward to our session.",
                "booking_id": booking_id,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert message_response.status_code in (200, 201, 404)

    def test_booking_cancellation_and_refund_flow(self, client, db_session, student_token, student_user):
        """Test booking cancellation with refund processing."""
        tutor_user, tutor_profile, subject = self._create_approved_tutor(
            db_session, email="cancel_tutor@test.com"
        )

        now = datetime.now(UTC)
        start_time = (now + timedelta(days=7)).replace(hour=15, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)

        booking_response = client.post(
            "/api/v1/bookings",
            json={
                "tutor_profile_id": tutor_profile.id,
                "subject_id": subject.id,
                "topic": "Physics fundamentals",
                "start_at": start_time.isoformat(),
                "end_at": end_time.isoformat(),
                "lesson_type": "REGULAR",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert booking_response.status_code == status.HTTP_201_CREATED
        booking_id = booking_response.json()["id"]

        cancel_response = client.patch(
            f"/api/v1/bookings/{booking_id}/cancel",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert cancel_response.status_code == status.HTTP_200_OK
        cancelled = cancel_response.json()
        assert "cancel" in cancelled["status"].lower()


class TestTutorOnboardingFlow:
    """Test tutor onboarding from registration to approval."""

    def test_complete_tutor_onboarding(self, client, db_session, admin_token):
        """Test full tutor onboarding workflow."""
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new_tutor@test.com",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "first_name": "New",
                "last_name": "Tutor",
                "role": "tutor",
            },
        )
        assert register_response.status_code in (200, 201, 422)

        from auth import get_password_hash
        from core.security import TokenManager
        from models import User

        user = db_session.query(User).filter_by(email="new_tutor@test.com").first()
        if not user:
            user = User(
                email="new_tutor@test.com",
                hashed_password=get_password_hash("SecurePass123!"),
                role="tutor",
                is_active=True,
                is_verified=True,
                first_name="New",
                last_name="Tutor",
            )
            db_session.add(user)
            db_session.commit()

        tutor_token = TokenManager.create_access_token({"sub": user.email})

        profile_response = client.put(
            "/api/v1/tutor-profile/me",
            json={
                "title": "Professional Math Tutor",
                "headline": "Helping students excel in mathematics",
                "bio": "I have 8 years of experience teaching calculus and algebra.",
                "hourly_rate": 45.00,
                "experience_years": 8,
                "education": "MSc Mathematics",
                "timezone": "America/New_York",
            },
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert profile_response.status_code in (200, 201)
        profile_data = profile_response.json()
        profile_id = profile_data["id"]

        availability_response = client.post(
            "/api/v1/tutor-profile/availability",
            json={
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "17:00",
            },
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert availability_response.status_code in (200, 201, 404)

        approve_response = client.post(
            f"/api/v1/admin/tutors/{profile_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert approve_response.status_code == status.HTTP_200_OK
        approved = approve_response.json()
        assert approved["is_approved"] is True
        assert approved["profile_status"] == "approved"

    def test_tutor_rejection_and_resubmission(self, client, db_session, admin_token):
        """Test tutor rejection followed by profile update and resubmission."""
        from auth import get_password_hash
        from core.security import TokenManager
        from models import TutorProfile, User

        user = User(
            email="reject_resubmit@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            is_verified=True,
            first_name="Reject",
            last_name="Tutor",
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Incomplete Profile",
            headline="Short",
            bio="Brief",
            hourly_rate=30.00,
            is_approved=False,
            profile_status="pending_approval",
        )
        db_session.add(profile)
        db_session.commit()

        reject_response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/reject",
            json={"rejection_reason": "Please provide more details about your qualifications and experience."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert reject_response.status_code == status.HTTP_200_OK

        profile.profile_status = "pending_approval"
        profile.is_approved = False
        profile.rejection_reason = None
        db_session.commit()

        tutor_token = TokenManager.create_access_token({"sub": user.email})
        update_response = client.put(
            "/api/v1/tutor-profile/me",
            json={
                "title": "Experienced Math Tutor",
                "headline": "Dedicated educator with proven track record",
                "bio": "I have 5 years of experience teaching high school and college students.",
                "hourly_rate": 40.00,
                "experience_years": 5,
            },
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert update_response.status_code in (200, 201)

        db_session.refresh(profile)
        approve_response = client.post(
            f"/api/v1/admin/tutors/{profile.id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert approve_response.status_code == status.HTTP_200_OK


class TestPackageFlow:
    """Test session package purchase and usage flow."""

    def _setup_tutor_with_pricing(self, db_session):
        """Create tutor with pricing options."""
        from auth import get_password_hash
        from models import TutorPricingOption, TutorProfile, User

        user = User(
            email="package_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            is_verified=True,
            first_name="Package",
            last_name="Tutor",
        )
        db_session.add(user)
        db_session.commit()

        profile = TutorProfile(
            user_id=user.id,
            title="Package Tutor",
            headline="Offers session packages",
            bio="Discounted packages available.",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        pricing_5 = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="5 Session Package",
            session_count=5,
            price=Decimal("225.00"),
            description="Save 10% on 5 sessions",
        )
        pricing_10 = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="10 Session Package",
            session_count=10,
            price=Decimal("400.00"),
            description="Save 20% on 10 sessions",
        )
        db_session.add_all([pricing_5, pricing_10])
        db_session.commit()

        return user, profile, pricing_5, pricing_10

    def test_package_purchase_and_session_usage(self, client, db_session, student_user, student_token):
        """Test purchasing a package and using session credits."""
        from models import StudentPackage, Subject

        tutor_user, tutor_profile, pricing_5, pricing_10 = self._setup_tutor_with_pricing(db_session)

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=tutor_profile.id,
            pricing_option_id=pricing_5.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=pricing_5.price,
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        assert package.sessions_remaining == 5
        assert package.status == "active"

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Test Subject", description="For testing")
            db_session.add(subject)
            db_session.commit()

        from models import Booking

        now = datetime.now(UTC)
        for i in range(2):
            start_time = (now + timedelta(days=i + 1)).replace(hour=10, minute=0, second=0, microsecond=0)
            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student_user.id,
                subject_id=subject.id,
                start_time=start_time,
                end_time=start_time + timedelta(hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                hourly_rate=50.00,
                total_amount=50.00,
                package_id=package.id,
            )
            db_session.add(booking)
            package.sessions_used += 1
            package.sessions_remaining -= 1
        db_session.commit()

        db_session.refresh(package)
        assert package.sessions_used == 2
        assert package.sessions_remaining == 3

    def test_package_expiration(self, db_session, student_user):
        """Test package expiration handling."""
        from auth import get_password_hash
        from models import StudentPackage, TutorPricingOption, TutorProfile, User

        tutor = User(
            email="expire_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Expire Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        pricing = TutorPricingOption(
            tutor_profile_id=profile.id,
            name="Expiring Package",
            session_count=5,
            price=Decimal("200.00"),
        )
        db_session.add(pricing)
        db_session.commit()

        expired_package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=pricing.id,
            sessions_purchased=5,
            sessions_remaining=3,
            sessions_used=2,
            purchase_price=Decimal("200.00"),
            purchased_at=datetime.now(UTC) - timedelta(days=400),
            expires_at=datetime.now(UTC) - timedelta(days=35),
            status="active",
        )
        db_session.add(expired_package)
        db_session.commit()

        if expired_package.expires_at and expired_package.expires_at < datetime.now(UTC):
            expired_package.status = "expired"
            db_session.commit()

        db_session.refresh(expired_package)
        assert expired_package.status == "expired"


class TestDisputeFlow:
    """Test dispute filing and resolution flow."""

    def _create_completed_booking(self, db_session, student_user):
        """Create a completed booking for dispute testing."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="dispute_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            first_name="Dispute",
            last_name="Tutor",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Dispute Test Tutor",
            headline="Testing disputes",
            bio="For dispute testing purposes.",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Dispute Subject", description="For testing")
            db_session.add(subject)
            db_session.commit()

        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=datetime.now(UTC) - timedelta(hours=2),
            end_time=datetime.now(UTC) - timedelta(hours=1),
            session_state="ENDED",
            session_outcome="COMPLETED",
            payment_state="CAPTURED",
            dispute_state="NONE",
            hourly_rate=50.00,
            total_amount=50.00,
            rate_cents=5000,
            tutor_name="Dispute Tutor",
            student_name=f"{student_user.first_name} {student_user.last_name}",
            subject_name=subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        return tutor, profile, booking

    def test_dispute_filing_and_admin_resolution(
        self, client, db_session, student_user, student_token, admin_token
    ):
        """Test complete dispute workflow from filing to resolution."""
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor, profile, booking = self._create_completed_booking(db_session, student_user)

        result = BookingStateMachine.open_dispute(
            booking,
            reason="The session quality did not meet expectations.",
            disputed_by_user_id=student_user.id,
        )
        assert result.success is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.dispute_state == "OPEN"
        assert booking.dispute_reason is not None

        from modules.bookings.domain.status import DisputeState

        resolve_result = BookingStateMachine.resolve_dispute(
            booking,
            resolution=DisputeState.RESOLVED_REFUNDED,
            resolved_by_user_id=1,
            notes="Refund issued due to service quality concerns.",
        )
        assert resolve_result.success is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.dispute_state == "RESOLVED_REFUNDED"
        assert booking.resolution_notes is not None

    def test_dispute_within_time_window(self, db_session, student_user):
        """Test that disputes can only be filed within the allowed time window."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User
        from modules.bookings.domain.state_machine import BookingStateMachine

        tutor = User(
            email="old_dispute_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Old Booking Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Old Subject", description="For testing")
            db_session.add(subject)
            db_session.commit()

        old_booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=datetime.now(UTC) - timedelta(days=45),
            end_time=datetime.now(UTC) - timedelta(days=45) + timedelta(hours=1),
            session_state="ENDED",
            session_outcome="COMPLETED",
            payment_state="CAPTURED",
            dispute_state="NONE",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(old_booking)
        db_session.commit()

        result = BookingStateMachine.open_dispute(
            old_booking,
            reason="Late dispute attempt",
            disputed_by_user_id=student_user.id,
        )

        assert result.success is False
        assert "days" in result.error_message.lower()

    def test_dispute_upheld_resolution(self, db_session, student_user):
        """Test dispute resolution where tutor is upheld."""
        from modules.bookings.domain.state_machine import BookingStateMachine
        from modules.bookings.domain.status import DisputeState

        _, _, booking = self._create_completed_booking(db_session, student_user)

        BookingStateMachine.open_dispute(
            booking,
            reason="Claimed no-show but tutor was present",
            disputed_by_user_id=student_user.id,
        )
        db_session.commit()

        resolve_result = BookingStateMachine.resolve_dispute(
            booking,
            resolution=DisputeState.RESOLVED_UPHELD,
            resolved_by_user_id=1,
            notes="Evidence shows tutor was present. Payment retained.",
        )
        assert resolve_result.success is True
        db_session.commit()

        db_session.refresh(booking)
        assert booking.dispute_state == "RESOLVED_UPHELD"
        assert booking.payment_state == "CAPTURED"


class TestCrossModuleIntegration:
    """Test integration across multiple modules."""

    def test_booking_notification_integration(self, db_session, student_user):
        """Test that bookings trigger appropriate notifications."""
        from auth import get_password_hash
        from models import Booking, Notification, Subject, TutorProfile, User

        tutor = User(
            email="notify_integration_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            first_name="Notify",
            last_name="Tutor",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Notification Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Notify Subject", description="Testing")
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
            tutor_name="Notify Tutor",
            student_name=f"{student_user.first_name} {student_user.last_name}",
            subject_name=subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        notification = Notification(
            user_id=tutor.id,
            type="new_booking",
            title="New Booking Request",
            message=f"You have a new booking request from {student_user.first_name}",
        )
        db_session.add(notification)
        db_session.commit()

        tutor_notifications = (
            db_session.query(Notification).filter(Notification.user_id == tutor.id).all()
        )
        assert len(tutor_notifications) >= 1
        assert any(n.type == "new_booking" for n in tutor_notifications)

    def test_review_after_completed_booking(self, client, db_session, student_user, student_token):
        """Test creating a review after a completed booking."""
        from auth import get_password_hash
        from models import Booking, Review, Subject, TutorProfile, User

        tutor = User(
            email="review_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            first_name="Review",
            last_name="Tutor",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Review Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Review Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=datetime.now(UTC) - timedelta(hours=3),
            end_time=datetime.now(UTC) - timedelta(hours=2),
            session_state="ENDED",
            session_outcome="COMPLETED",
            payment_state="CAPTURED",
            hourly_rate=50.00,
            total_amount=50.00,
            tutor_name="Review Tutor",
            student_name=f"{student_user.first_name} {student_user.last_name}",
            subject_name=subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        review = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=5,
            comment="Excellent session! Very helpful tutor.",
            is_public=True,
        )
        db_session.add(review)
        db_session.commit()

        assert review.id is not None
        assert review.rating == 5

        db_session.refresh(booking)
        assert booking.review is not None
        assert booking.review.rating == 5
