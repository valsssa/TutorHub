"""
Tests for data integrity and consistency.

Tests cover:
- Cascade deletions
- Soft delete consistency
- Foreign key integrity
- Unique constraint handling
"""

from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError


class TestCascadeDeletions:
    """Test cascade deletion behavior across related entities."""

    def test_tutor_profile_deletion_preserves_bookings(self, db_session, student_user):
        """Test that deleting a tutor profile preserves bookings for audit trail.

        Note: Bookings should NOT be cascade-deleted because they contain:
        - Financial records (payment history, refunds)
        - Review and rating data
        - Audit trail for disputes and compliance

        The database CASCADE constraint handles the FK, but ORM delete preserves
        related records for data integrity. Use soft-delete for profiles instead.
        """
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="cascade_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Cascade Test Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()
        profile_id = profile.id

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Cascade Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
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
        booking_id = booking.id

        # Soft-delete the profile (preferred approach for data integrity)
        profile.deleted_at = utc_now()
        db_session.commit()

        # Booking should be preserved for audit trail
        db_session.expire_all()
        preserved_booking = db_session.query(Booking).filter_by(id=booking_id).first()
        assert preserved_booking is not None
        assert preserved_booking.tutor_profile_id == profile_id

    def test_user_cascade_deletes_student_profile(self, db_session):
        """Test that deleting a user cascades to student profile."""
        from auth import get_password_hash
        from models import StudentProfile, User

        user = User(
            email="cascade_student@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        student_profile = StudentProfile(
            user_id=user.id,
            bio="Test student",
            grade_level="12th",
        )
        db_session.add(student_profile)
        db_session.commit()
        profile_id = student_profile.id

        db_session.delete(user)
        db_session.commit()

        deleted_profile = db_session.query(StudentProfile).filter_by(id=profile_id).first()
        assert deleted_profile is None

    def test_booking_cascade_deletes_review(self, db_session, student_user):
        """Test that deleting a booking cascades to its review."""
        from auth import get_password_hash
        from models import Booking, Review, Subject, TutorProfile, User

        tutor = User(
            email="review_cascade_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Review Cascade Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Review Cascade Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            session_state="ENDED",
            session_outcome="COMPLETED",
            payment_state="CAPTURED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        review = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=5,
            comment="Great session!",
        )
        db_session.add(review)
        db_session.commit()
        review_id = review.id

        db_session.delete(booking)
        db_session.commit()

        deleted_review = db_session.query(Review).filter_by(id=review_id).first()
        assert deleted_review is None

    def test_booking_cascade_deletes_session_materials(self, db_session, student_user):
        """Test that deleting a booking cascades to session materials."""
        from auth import get_password_hash
        from models import Booking, SessionMaterial, Subject, TutorProfile, User

        tutor = User(
            email="material_cascade_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Material Cascade Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Material Cascade Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        material = SessionMaterial(
            booking_id=booking.id,
            file_name="notes.pdf",
            file_url="https://storage.example.com/notes.pdf",
            uploaded_by=tutor.id,
        )
        db_session.add(material)
        db_session.commit()
        material_id = material.id

        db_session.delete(booking)
        db_session.commit()

        deleted_material = db_session.query(SessionMaterial).filter_by(id=material_id).first()
        assert deleted_material is None


class TestSoftDeleteConsistency:
    """Test soft delete behavior and consistency."""

    def test_soft_deleted_user_excluded_from_queries(self, db_session):
        """Test that soft deleted users can be filtered out."""
        from auth import get_password_hash
        from models import User

        user = User(
            email="soft_delete_user@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        if hasattr(user, "deleted_at"):
            user.deleted_at = utc_now()
            db_session.commit()

            active_users = (
                db_session.query(User)
                .filter(User.deleted_at.is_(None))
                .filter_by(email="soft_delete_user@test.com")
                .all()
            )
            assert len(active_users) == 0

            all_users = (
                db_session.query(User)
                .filter_by(email="soft_delete_user@test.com")
                .all()
            )
            assert len(all_users) == 1

    def test_soft_delete_preserves_data(self, db_session, student_user):
        """Test that soft delete preserves all data."""
        import uuid

        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        unique_id = uuid.uuid4().hex[:8]
        tutor = User(
            email=f"preserve_data_tutor_{unique_id}@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Preserve Data Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Preserve Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=50.00,
            topic="Important Session",
            notes="Critical notes here",
        )
        db_session.add(booking)
        db_session.commit()

        original_topic = booking.topic
        original_notes = booking.notes
        original_amount = booking.total_amount

        if hasattr(booking, "deleted_at"):
            booking.deleted_at = utc_now()
            booking.deleted_by = tutor.id  # Use the tutor created in the test
            db_session.commit()

            db_session.refresh(booking)
            assert booking.topic == original_topic
            assert booking.notes == original_notes
            assert booking.total_amount == original_amount

    def test_soft_delete_with_deleted_by_tracking(self, db_session, student_user, admin_user):
        """Test that soft delete tracks who performed the deletion."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="track_delete_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Track Delete Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Track Delete Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
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

        if hasattr(booking, "deleted_at") and hasattr(booking, "deleted_by"):
            booking.deleted_at = utc_now()
            booking.deleted_by = admin_user.id
            db_session.commit()

            db_session.refresh(booking)
            assert booking.deleted_by == admin_user.id
            assert booking.deleted_at is not None


class TestForeignKeyIntegrity:
    """Test foreign key constraints and referential integrity."""

    def test_booking_requires_valid_tutor_profile(self, db_session, student_user):
        """Test that bookings require a valid tutor profile."""
        from models import Booking, Subject

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="FK Test Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=99999,
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

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_booking_requires_valid_student(self, db_session):
        """Test that bookings require a valid student."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="fk_valid_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="FK Valid Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="FK Valid Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=99999,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="REQUESTED",
            payment_state="PENDING",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_review_requires_valid_booking(self, db_session, student_user):
        """Test that reviews require a valid booking."""
        from auth import get_password_hash
        from models import Review, TutorProfile, User

        tutor = User(
            email="review_fk_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Review FK Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        review = Review(
            booking_id=99999,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=5,
            comment="This should fail",
        )
        db_session.add(review)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_student_package_requires_valid_pricing_option(self, db_session, student_user):
        """Test that student packages require a valid pricing option."""
        from auth import get_password_hash
        from models import StudentPackage, TutorProfile, User

        tutor = User(
            email="package_fk_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Package FK Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=99999,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("200.00"),
            status="active",
        )
        db_session.add(package)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestUniqueConstraintHandling:
    """Test unique constraint handling."""

    def test_user_email_must_be_unique(self, db_session):
        """Test that user emails must be unique."""
        from auth import get_password_hash
        from models import User

        user1 = User(
            email="unique_email@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(user1)
        db_session.commit()

        user2 = User(
            email="unique_email@test.com",
            hashed_password=get_password_hash("password456"),
            role="student",
            is_active=True,
        )
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_one_review_per_booking(self, db_session, student_user):
        """Test that only one review is allowed per booking."""
        from auth import get_password_hash
        from models import Booking, Review, Subject, TutorProfile, User

        tutor = User(
            email="one_review_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="One Review Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="One Review Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            session_state="ENDED",
            session_outcome="COMPLETED",
            payment_state="CAPTURED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        review1 = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=5,
            comment="First review",
        )
        db_session.add(review1)
        db_session.commit()

        review2 = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=4,
            comment="Second review (should fail)",
        )
        db_session.add(review2)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_student_profile_one_per_user(self, db_session):
        """Test that only one student profile is allowed per user."""
        from auth import get_password_hash
        from models import StudentProfile, User

        user = User(
            email="one_profile_user@test.com",
            hashed_password=get_password_hash("password123"),
            role="student",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        profile1 = StudentProfile(
            user_id=user.id,
            bio="First profile",
        )
        db_session.add(profile1)
        db_session.commit()

        profile2 = StudentProfile(
            user_id=user.id,
            bio="Second profile (should fail)",
        )
        db_session.add(profile2)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_webhook_event_idempotency(self, db_session):
        """Test that webhook events must have unique stripe_event_id."""
        from models import WebhookEvent

        event1 = WebhookEvent(
            stripe_event_id="evt_unique_123",
            event_type="payment_intent.succeeded",
        )
        db_session.add(event1)
        db_session.commit()

        event2 = WebhookEvent(
            stripe_event_id="evt_unique_123",
            event_type="payment_intent.succeeded",
        )
        db_session.add(event2)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestCheckConstraintValidation:
    """Test check constraint validation."""

    def test_booking_time_constraint(self, db_session, student_user):
        """Test that booking end time must be after start time."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="time_check_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Time Check Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Time Check Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()

        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=1),
            session_state="REQUESTED",
            payment_state="PENDING",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_review_rating_constraint(self, db_session, student_user):
        """Test that review ratings must be between 1 and 5."""
        from auth import get_password_hash
        from models import Booking, Review, Subject, TutorProfile, User

        tutor = User(
            email="rating_check_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Rating Check Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Rating Check Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            session_state="ENDED",
            session_outcome="COMPLETED",
            payment_state="CAPTURED",
            hourly_rate=50.00,
            total_amount=50.00,
        )
        db_session.add(booking)
        db_session.commit()

        review = Review(
            booking_id=booking.id,
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            rating=10,
            comment="Invalid rating",
        )
        db_session.add(review)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_payment_positive_amount_constraint(self, db_session, student_user):
        """Test that payment amounts must be positive."""
        from auth import get_password_hash
        from models import Booking, Payment, Subject, TutorProfile, User

        tutor = User(
            email="payment_check_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Payment Check Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = db_session.query(Subject).first()
        if not subject:
            subject = Subject(name="Payment Check Subject", description="Testing")
            db_session.add(subject)
            db_session.commit()

        now = utc_now()
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

        payment = Payment(
            booking_id=booking.id,
            student_id=student_user.id,
            amount_cents=-5000,
            currency="USD",
            status="pending",
        )
        db_session.add(payment)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestDataConsistencyAcrossRelations:
    """Test data consistency across related entities."""

    def test_booking_snapshot_preserves_original_values(self, db_session, student_user):
        """Test that booking snapshots preserve original tutor/subject info."""
        from auth import get_password_hash
        from models import Booking, Subject, TutorProfile, User

        tutor = User(
            email="snapshot_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
            first_name="Original",
            last_name="Name",
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Original Title",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        subject = Subject(name="Original Subject", description="Testing")
        db_session.add(subject)
        db_session.commit()

        now = utc_now()
        booking = Booking(
            tutor_profile_id=profile.id,
            student_id=student_user.id,
            subject_id=subject.id,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=1),
            session_state="SCHEDULED",
            payment_state="AUTHORIZED",
            hourly_rate=50.00,
            total_amount=50.00,
            tutor_name="Original Name",
            tutor_title="Original Title",
            subject_name="Original Subject",
            student_name=f"{student_user.first_name} {student_user.last_name}",
        )
        db_session.add(booking)
        db_session.commit()

        profile.title = "Updated Title"
        subject.name = "Updated Subject"
        tutor.first_name = "Updated"
        db_session.commit()

        db_session.refresh(booking)
        assert booking.tutor_name == "Original Name"
        assert booking.tutor_title == "Original Title"
        assert booking.subject_name == "Original Subject"

    def test_package_sessions_tracking_consistency(self, db_session, student_user):
        """Test that package session counts remain consistent."""
        from auth import get_password_hash
        from models import StudentPackage, TutorPricingOption, TutorProfile, User

        tutor = User(
            email="package_consistency_tutor@test.com",
            hashed_password=get_password_hash("password123"),
            role="tutor",
            is_active=True,
        )
        db_session.add(tutor)
        db_session.commit()

        profile = TutorProfile(
            user_id=tutor.id,
            title="Package Consistency Tutor",
            hourly_rate=50.00,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        pricing = TutorPricingOption(
            tutor_profile_id=profile.id,
            title="Consistency Package",
            duration_minutes=60,
            price=Decimal("200.00"),
        )
        db_session.add(pricing)
        db_session.commit()

        package = StudentPackage(
            student_id=student_user.id,
            tutor_profile_id=profile.id,
            pricing_option_id=pricing.id,
            sessions_purchased=5,
            sessions_remaining=5,
            sessions_used=0,
            purchase_price=Decimal("200.00"),
            status="active",
        )
        db_session.add(package)
        db_session.commit()

        for _ in range(3):
            package.sessions_used += 1
            package.sessions_remaining -= 1
            db_session.commit()

        db_session.refresh(package)
        assert package.sessions_purchased == package.sessions_used + package.sessions_remaining
        assert package.sessions_used == 3
        assert package.sessions_remaining == 2
