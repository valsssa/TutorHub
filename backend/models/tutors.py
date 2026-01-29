"""Tutor-related models."""

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, JSONEncodedArray


class TutorProfile(Base):
    """Tutor profile and metrics."""

    __tablename__ = "tutor_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    title = Column(String(200), nullable=False)
    headline = Column(String(255))
    bio = Column(Text)
    description = Column(Text)
    hourly_rate = Column(DECIMAL(10, 2), nullable=False)
    experience_years = Column(Integer, default=0)
    education = Column(String(255))
    languages = Column(JSONEncodedArray)
    video_url = Column(String(500))
    is_approved = Column(Boolean, default=False)
    profile_status = Column(String(20), nullable=False, default="incomplete")
    rejection_reason = Column(Text)
    approved_at = Column(TIMESTAMP(timezone=True))
    approved_by = Column(Integer)  # Admin user ID who approved (no FK to avoid ambiguity)
    average_rating = Column(DECIMAL(3, 2), default=0.00)
    total_reviews = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    timezone = Column(String(64), default="UTC")  # Phase 3: Tutor timezone
    currency = Column(String(3), nullable=False, default="USD", server_default="USD")
    # Booking configuration fields (from init.sql schema)
    auto_confirm_threshold_hours = Column(Integer, default=24)
    auto_confirm = Column(Boolean, default=False)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Enhanced booking fields (optional - require migration 017)
    # cancellation_strikes = Column(Integer, default=0)
    # auto_confirm = Column(Boolean, default=False)
    # trial_price_cents = Column(Integer)
    # payout_method = Column(Text)
    # Stripe Connect integration
    stripe_account_id = Column(String(255), nullable=True, index=True)  # acct_...
    stripe_charges_enabled = Column(Boolean, default=False)
    stripe_payouts_enabled = Column(Boolean, default=False)
    stripe_onboarding_completed = Column(Boolean, default=False)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    # Relationships
    user = relationship("User", back_populates="tutor_profile", foreign_keys=[user_id])
    subjects = relationship("TutorSubject", back_populates="tutor_profile", cascade="all, delete-orphan")
    availabilities = relationship(
        "TutorAvailability",
        back_populates="tutor_profile",
        cascade="all, delete-orphan",
    )
    certifications = relationship(
        "TutorCertification",
        back_populates="tutor_profile",
        cascade="all, delete-orphan",
    )
    educations = relationship("TutorEducation", back_populates="tutor_profile", cascade="all, delete-orphan")
    pricing_options = relationship(
        "TutorPricingOption",
        back_populates="tutor_profile",
        cascade="all, delete-orphan",
    )
    bookings = relationship("Booking", back_populates="tutor_profile")
    reviews = relationship("Review", back_populates="tutor_profile")
    favorites = relationship("FavoriteTutor", back_populates="tutor_profile", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("hourly_rate > 0", name="positive_rate"),
        CheckConstraint("average_rating BETWEEN 0 AND 5", name="valid_rating"),
        CheckConstraint(
            "profile_status IN ('incomplete', 'pending_approval', 'under_review', 'approved', 'rejected')",
            name="valid_profile_status",
        ),
    )


class TutorSubject(Base):
    """Tutor subject specializations."""

    __tablename__ = "tutor_subjects"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"))
    proficiency_level = Column(String(20), default="B2")  # Phase 3: CEFR default
    years_experience = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="subjects")
    subject = relationship("Subject", back_populates="tutor_subjects")

    __table_args__ = (
        CheckConstraint(
            "proficiency_level IN ('native', 'c2', 'c1', 'b2', 'b1', 'a2', 'a1')",  # Phase 3: CEFR levels (lowercase)
            name="valid_proficiency",
        ),
    )


class TutorCertification(Base):
    """Tutor certifications."""

    __tablename__ = "tutor_certifications"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255))
    issue_date = Column(Date)
    expiration_date = Column(Date)
    credential_id = Column(String(100))
    credential_url = Column(String(500))
    document_url = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    tutor_profile = relationship("TutorProfile", back_populates="certifications")


class TutorEducation(Base):
    """Tutor education history."""

    __tablename__ = "tutor_education"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    institution = Column(String(255), nullable=False)
    degree = Column(String(255))
    field_of_study = Column(String(255))
    start_year = Column(Integer)
    end_year = Column(Integer)
    description = Column(Text)
    document_url = Column(String(500))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    tutor_profile = relationship("TutorProfile", back_populates="educations")


class TutorPricingOption(Base):
    """Tutor pricing options."""

    __tablename__ = "tutor_pricing_options"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    validity_days = Column(Integer, nullable=True)  # Number of days package is valid (NULL = no expiration)
    extend_on_use = Column(Boolean, default=False, nullable=False)  # Rolling expiry: extend validity on each use
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    tutor_profile = relationship("TutorProfile", back_populates="pricing_options")

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="positive_duration"),
        CheckConstraint("price > 0", name="positive_price"),
        CheckConstraint("validity_days IS NULL OR validity_days > 0", name="positive_validity_days"),
    )


class TutorAvailability(Base):
    """Recurring weekly availability windows for tutors."""

    __tablename__ = "tutor_availabilities"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_recurring = Column(Boolean, nullable=False, default=True)
    # Timezone in which start_time/end_time are expressed (IANA timezone, e.g., "America/New_York")
    # This enables proper DST handling when converting to UTC for slot generation
    timezone = Column(String(64), nullable=False, default="UTC", server_default="UTC")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="availabilities")

    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="tutor_availabilities_day_of_week_check"),
        CheckConstraint("start_time < end_time", name="chk_availability_time_order"),
    )


class TutorBlackout(Base):
    """Temporary unavailable periods (vacations, etc.)."""

    __tablename__ = "tutor_blackouts"

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_at = Column(TIMESTAMP(timezone=True), nullable=False)
    end_at = Column(TIMESTAMP(timezone=True), nullable=False)
    reason = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    tutor = relationship("User", foreign_keys=[tutor_id])

    __table_args__ = (CheckConstraint("start_at < end_at", name="valid_blackout_time"),)


class TutorMetrics(Base):
    """Aggregated tutor performance metrics."""

    __tablename__ = "tutor_metrics"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Response metrics
    avg_response_time_minutes = Column(Integer, default=0)
    response_rate_24h = Column(DECIMAL(5, 2), default=0.00)

    # Booking metrics
    total_bookings = Column(Integer, default=0)
    completed_bookings = Column(Integer, default=0)
    cancelled_bookings = Column(Integer, default=0)
    no_show_bookings = Column(Integer, default=0)
    completion_rate = Column(DECIMAL(5, 2), default=0.00)

    # Student metrics
    total_unique_students = Column(Integer, default=0)
    returning_students = Column(Integer, default=0)
    student_retention_rate = Column(DECIMAL(5, 2), default=0.00)
    avg_sessions_per_student = Column(DECIMAL(5, 2), default=0.00)

    # Revenue metrics
    total_revenue = Column(DECIMAL(12, 2), default=0.00)
    avg_session_value = Column(DECIMAL(10, 2), default=0.00)

    # Engagement metrics
    profile_views_30d = Column(Integer, default=0)
    booking_conversion_rate = Column(DECIMAL(5, 2), default=0.00)

    # Rating metrics
    avg_rating = Column(DECIMAL(3, 2), default=0.00)
    total_reviews = Column(Integer, default=0)

    # Percentile rankings
    response_time_percentile = Column(Integer)
    retention_rate_percentile = Column(Integer)
    rating_percentile = Column(Integer)

    # Timestamps
    last_calculated = Column(TIMESTAMP(timezone=True), server_default=func.now())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    tutor_profile = relationship("TutorProfile", backref="metrics", uselist=False)

    __table_args__ = (
        CheckConstraint(
            "(response_time_percentile IS NULL OR response_time_percentile BETWEEN 0 AND 100)",
            name="valid_response_percentile",
        ),
        CheckConstraint(
            "(retention_rate_percentile IS NULL OR retention_rate_percentile BETWEEN 0 AND 100)",
            name="valid_retention_percentile",
        ),
        CheckConstraint(
            "(rating_percentile IS NULL OR rating_percentile BETWEEN 0 AND 100)",
            name="valid_rating_percentile",
        ),
    )


class TutorResponseLog(Base):
    """Log of tutor responses to booking requests for response time tracking."""

    __tablename__ = "tutor_response_log"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"))
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    booking_created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    tutor_responded_at = Column(TIMESTAMP(timezone=True))
    response_time_minutes = Column(Integer)
    response_action = Column(String(20))  # confirmed, cancelled, ignored, auto_confirmed
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    booking = relationship("Booking")
    tutor_profile = relationship("TutorProfile")
    student = relationship("User")

    __table_args__ = (
        CheckConstraint(
            "response_action IN ('confirmed', 'cancelled', 'ignored', 'auto_confirmed')",
            name="valid_response_action",
        ),
    )
