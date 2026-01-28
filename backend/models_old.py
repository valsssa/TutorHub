"""SQLAlchemy database models."""

import json

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
    TypeDecorator,
)
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class JSONEncodedArray(TypeDecorator):
    """
    Array type that works for both PostgreSQL (native ARRAY)
    and SQLite (JSON-encoded string).
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_ARRAY(Text))
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if dialect.name == "postgresql":
            return value if value else []
        return json.loads(value) if value else []


class User(Base):
    """User authentication model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    avatar_key = Column(String(255), nullable=True, index=True)
    currency = Column(String(3), nullable=False, default="USD", server_default="USD")
    timezone = Column(String(64), nullable=False, default="UTC", server_default="UTC")
    preferred_language = Column(String(5), nullable=False, default="en", server_default="en")
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="UserProfile.user_id",
    )
    tutor_profile = relationship(
        "TutorProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="TutorProfile.user_id",
    )
    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="StudentProfile.user_id",
    )
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint("role IN ('student', 'tutor', 'admin')", name="valid_role"),)


class UserProfile(Base):
    """Extended user profile."""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    bio = Column(Text)
    timezone = Column(String(64), default="UTC")
    # Phase 3: struct.txt compliance fields
    country_of_birth = Column(String(2))  # ISO 3166-1 alpha-2
    phone_country_code = Column(String(5))  # E.164 format (+1 to +999)
    date_of_birth = Column(Date)  # For age verification
    age_confirmed = Column(Boolean, default=False, nullable=False)  # 18+ confirmation
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="profile")


class Subject(Base):
    """Subject catalog."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    tutor_subjects = relationship("TutorSubject", back_populates="subject", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="subject")


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
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Enhanced booking fields (optional - require migration 017)
    # cancellation_strikes = Column(Integer, default=0)
    # auto_confirm = Column(Boolean, default=False)
    # trial_price_cents = Column(Integer)
    # payout_method = Column(Text)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

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
            "proficiency_level IN ('Native', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1')",  # Phase 3: CEFR levels
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
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

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
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

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
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    tutor_profile = relationship("TutorProfile", back_populates="pricing_options")

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="positive_duration"),
        CheckConstraint("price > 0", name="positive_price"),
    )


class StudentProfile(Base):
    """Student profile."""

    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    bio = Column(Text)
    grade_level = Column(String(50))
    school_name = Column(String(200))
    learning_goals = Column(Text)
    interests = Column(Text)
    total_sessions = Column(Integer, default=0)
    credit_balance_cents = Column(Integer, default=0)
    preferred_language = Column(String(10))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="student_profile")


class Booking(Base):
    """Tutoring session bookings."""

    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"))
    # package_id - Not in production DB (requires migration 017)
    # package_id = Column(Integer, ForeignKey("student_packages.id"), nullable=True)
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    topic = Column(String(255))
    notes = Column(Text)
    meeting_url = Column(String(500))
    # Pricing fields (production schema)
    hourly_rate = Column(DECIMAL(10, 2), nullable=False)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    pricing_option_id = Column(Integer, nullable=True)  # FK to tutor_pricing_options
    package_sessions_remaining = Column(Integer, nullable=True)
    pricing_type = Column(String(20), default="hourly", nullable=False)
    lesson_type = Column(String(20), default="REGULAR", nullable=False)
    created_by = Column(String(20), default="STUDENT", nullable=False)
    # Immutable snapshot fields (production schema)
    tutor_name = Column(String(200), nullable=True)
    tutor_title = Column(String(200), nullable=True)
    student_name = Column(String(200), nullable=True)
    subject_name = Column(String(100), nullable=True)
    pricing_snapshot = Column(Text, nullable=True)  # JSONB in DB
    agreement_terms = Column(Text, nullable=True)
    # Instant booking fields (production schema)
    is_instant_booking = Column(Boolean, default=False)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    confirmed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    is_rebooked = Column(Boolean, default=False)
    original_booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tutor_profile = relationship("TutorProfile", back_populates="bookings")
    student = relationship("User", foreign_keys=[student_id])
    subject = relationship("Subject", back_populates="bookings")
    # package relationship requires migration 017
    # package = relationship("StudentPackage", foreign_keys=[package_id])
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


class Review(Base):
    """Tutor reviews and ratings."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), unique=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    is_public = Column(Boolean, default=True)
    booking_snapshot = Column(Text, nullable=True)  # JSONB immutable context
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="review")
    tutor_profile = relationship("TutorProfile", back_populates="reviews")
    student = relationship("User", foreign_keys=[student_id])

    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="valid_rating_value"),)


class Message(Base):
    """In-platform messaging."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    booking = relationship("Booking", back_populates="messages")


class Notification(Base):
    """User notifications."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500))
    is_read = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")


class FavoriteTutor(Base):
    """Student favorite tutors."""

    __tablename__ = "favorite_tutors"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    tutor_profile = relationship("TutorProfile", back_populates="favorites")


class Report(Base):
    """User reports for moderation."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    reported_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    booking = relationship("Booking", foreign_keys=[booking_id])

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'reviewed', 'resolved', 'dismissed')",
            name="valid_report_status",
        ),
    )


# Add to models.py after existing classes


class SupportedCurrency(Base):
    """Currency options supported by the platform."""

    __tablename__ = "supported_currencies"

    currency_code = Column(String(3), primary_key=True)
    currency_name = Column(String(50), nullable=False)
    currency_symbol = Column(String(10), nullable=False)
    decimal_places = Column(Integer, default=2)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class AuditLog(Base):
    """Audit trail for all data changes."""

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)
    old_data = Column(Text)  # JSONB stored as text for SQLAlchemy compatibility
    new_data = Column(Text)  # JSONB stored as text for SQLAlchemy compatibility
    changed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    changed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)

    # Relationships
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    __table_args__ = (
        CheckConstraint(
            "action IN ('INSERT', 'UPDATE', 'DELETE', 'SOFT_DELETE', 'RESTORE')",
            name="valid_audit_action",
        ),
    )


class StudentPackage(Base):
    """Student-purchased packages and subscriptions."""

    __tablename__ = "student_packages"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    pricing_option_id = Column(
        Integer,
        ForeignKey("tutor_pricing_options.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sessions_purchased = Column(Integer, nullable=False)
    sessions_remaining = Column(Integer, nullable=False)
    sessions_used = Column(Integer, default=0, nullable=False)
    purchase_price = Column(DECIMAL(10, 2), nullable=False)
    purchased_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    payment_intent_id = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    tutor_profile = relationship("TutorProfile", foreign_keys="StudentPackage.tutor_profile_id")
    pricing_option = relationship("TutorPricingOption", foreign_keys="StudentPackage.pricing_option_id")

    __table_args__ = (
        CheckConstraint("sessions_purchased > 0", name="positive_sessions_purchased"),
        CheckConstraint("sessions_remaining >= 0", name="non_negative_sessions_remaining"),
        CheckConstraint("sessions_used >= 0", name="non_negative_sessions_used"),
        CheckConstraint("purchase_price > 0", name="positive_purchase_price"),
        CheckConstraint(
            "status IN ('active', 'expired', 'exhausted', 'refunded')",
            name="valid_package_status",
        ),
    )


class Payment(Base):
    """Payment transactions for bookings and packages."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    provider = Column(String(20), default="stripe", nullable=False)
    provider_payment_id = Column(Text)
    status = Column(String(30), default="REQUIRES_ACTION", nullable=False)
    payment_metadata = Column(Text)  # JSONB stored as text, renamed to avoid SQLAlchemy conflict
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="payments")
    student = relationship("User", foreign_keys=[student_id])
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_payment_amount"),
        CheckConstraint(
            "provider IN ('stripe', 'adyen', 'paypal', 'test')",
            name="valid_payment_provider",
        ),
        CheckConstraint(
            "status IN ('REQUIRES_ACTION', 'AUTHORIZED', 'CAPTURED', 'REFUNDED', 'FAILED')",
            name="valid_payment_status",
        ),
    )


class Refund(Base):
    """Refund transactions linked to payments."""

    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"))
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    reason = Column(String(30), nullable=False)
    provider_refund_id = Column(Text)
    refund_metadata = Column(Text)  # JSONB stored as text, renamed to avoid SQLAlchemy conflict
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    payment = relationship("Payment", back_populates="refunds")
    booking = relationship("Booking", foreign_keys=[booking_id])

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_refund_amount"),
        CheckConstraint(
            "reason IN ('STUDENT_CANCEL', 'TUTOR_CANCEL', 'NO_SHOW_TUTOR', 'GOODWILL', 'OTHER')",
            name="valid_refund_reason",
        ),
    )


class Payout(Base):
    """Tutor earnings payout batches."""

    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True)
    tutor_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    transfer_reference = Column(Text)
    payout_metadata = Column(Text)  # JSONB stored as text, renamed to avoid SQLAlchemy conflict
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tutor = relationship("User", foreign_keys=[tutor_id])

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="positive_payout_amount"),
        CheckConstraint(
            "status IN ('PENDING', 'SUBMITTED', 'PAID', 'FAILED')",
            name="valid_payout_status",
        ),
        CheckConstraint("period_start <= period_end", name="valid_payout_period"),
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
