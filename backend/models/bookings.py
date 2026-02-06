"""Booking and session models."""

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, JSONType


class Booking(Base):
    """Tutoring session bookings."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"))
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)

    # Optimistic locking version for race condition prevention
    version = Column(Integer, default=1, nullable=False)

    # Four independent status fields (booking flow redesign)
    session_state = Column(String(20), default="REQUESTED", nullable=False)
    session_outcome = Column(String(30), nullable=True)  # Set on terminal states
    payment_state = Column(String(30), default="PENDING", nullable=False)
    dispute_state = Column(String(30), default="NONE", nullable=False)

    # Dispute tracking fields
    dispute_reason = Column(Text, nullable=True)
    disputed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    disputed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Cancellation tracking
    cancelled_by_role = Column(String(20), nullable=True)  # STUDENT, TUTOR, ADMIN, SYSTEM
    topic = Column(String(255))
    notes = Column(Text)
    notes_student = Column(Text)
    notes_tutor = Column(Text)
    meeting_url = Column(String(500))
    join_url = Column(Text)  # Meeting URL for virtual sessions
    # Pricing fields (production schema)
    hourly_rate = Column(DECIMAL(10, 2), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    rate_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    platform_fee_pct = Column(DECIMAL(5, 2), default=20.0, nullable=False)
    platform_fee_cents = Column(Integer, default=0, nullable=False)
    tutor_earnings_cents = Column(Integer, default=0, nullable=False)
    pricing_option_id = Column(Integer, ForeignKey("tutor_pricing_options.id", ondelete="SET NULL"), nullable=True)
    package_id = Column(Integer, ForeignKey("student_packages.id", ondelete="SET NULL"), nullable=True)
    package_sessions_remaining = Column(Integer, nullable=True)
    pricing_type = Column(String(20), default="hourly", nullable=False)
    lesson_type = Column(String(20), default="REGULAR", nullable=False)
    student_tz = Column(String(64), default="UTC", nullable=False)
    tutor_tz = Column(String(64), default="UTC", nullable=False)
    created_by = Column(String(20), default="STUDENT", nullable=False)
    # Immutable snapshot fields (production schema)
    tutor_name = Column(String(200), nullable=True)
    tutor_title = Column(String(200), nullable=True)
    student_name = Column(String(200), nullable=True)
    subject_name = Column(String(100), nullable=True)
    pricing_snapshot = Column(JSONType, nullable=True)
    agreement_terms = Column(Text, nullable=True)
    # Instant booking fields (production schema)
    is_instant_booking = Column(Boolean, default=False)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    confirmed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_rebooked = Column(Boolean, default=False)
    original_booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    # Stripe integration
    stripe_checkout_session_id = Column(String(255), nullable=True, index=True)
    # Zoom integration
    zoom_meeting_id = Column(String(255), nullable=True, index=True)
    zoom_meeting_pending = Column(Boolean, default=False, nullable=False)  # Flag for retry when Zoom fails
    # Google Calendar integration
    google_calendar_event_id = Column(String(255), nullable=True)
    # Session attendance tracking (for attendance-based outcome determination)
    tutor_joined_at = Column(TIMESTAMP(timezone=True), nullable=True)
    student_joined_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # Video meeting provider tracking
    video_provider = Column(String(20), nullable=True)  # zoom, google_meet, teams, custom, manual
    google_meet_link = Column(String(500), nullable=True)  # Separate from join_url for Meet-specific links
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="bookings")
    student = relationship("User", foreign_keys=[student_id])
    subject = relationship("Subject", back_populates="bookings")
    # Package relationship for session packages
    package = relationship("StudentPackage", foreign_keys=[package_id])
    # Keep these relationships if tables exist (check production schema)
    materials = relationship(
        "SessionMaterial",
        back_populates="booking",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    review = relationship(
        "Review",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    messages = relationship("Message", back_populates="booking", passive_deletes=True)
    payments = relationship("Payment", back_populates="booking", passive_deletes=True)

    __table_args__ = (
        CheckConstraint("start_time < end_time", name="valid_booking_time"),
        CheckConstraint(
            "lesson_type IN ('TRIAL', 'REGULAR', 'PACKAGE')",
            name="valid_lesson_type",
        ),
        CheckConstraint(
            "created_by IN ('STUDENT', 'TUTOR', 'ADMIN')",
            name="valid_created_by",
        ),
        CheckConstraint(
            "session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE', 'ENDED', 'CANCELLED', 'EXPIRED')",
            name="valid_session_state",
        ),
        CheckConstraint(
            "session_outcome IS NULL OR session_outcome IN ('COMPLETED', 'NOT_HELD', 'NO_SHOW_STUDENT', 'NO_SHOW_TUTOR')",
            name="valid_session_outcome",
        ),
        CheckConstraint(
            "payment_state IN ('PENDING', 'AUTHORIZED', 'CAPTURED', 'VOIDED', 'REFUNDED', 'PARTIALLY_REFUNDED')",
            name="valid_payment_state",
        ),
        CheckConstraint(
            "dispute_state IN ('NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_REFUNDED')",
            name="valid_dispute_state",
        ),
        CheckConstraint(
            "cancelled_by_role IS NULL OR cancelled_by_role IN ('STUDENT', 'TUTOR', 'ADMIN', 'SYSTEM')",
            name="valid_cancelled_by_role",
        ),
    )


class SessionMaterial(Base):
    """Session materials and attachments."""

    __tablename__ = "session_materials"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"))
    file_name = Column(String(255))
    file_url = Column(String(500))
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="materials")
    uploader = relationship("User", foreign_keys=[uploaded_by])
