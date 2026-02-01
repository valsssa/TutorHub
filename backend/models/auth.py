"""User authentication and profile models."""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    """User authentication model.

    User Identity Contract:
    - first_name: Required for complete profile, max 100 chars
    - last_name: Required for complete profile, max 100 chars
    - profile_incomplete: TRUE if user needs to complete profile (missing names)

    All registered users must have both first_name and last_name.
    OAuth users may be created with profile_incomplete=TRUE and must
    complete their profile on first login.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    # Profile completion flag - TRUE if user needs to provide missing names
    profile_incomplete = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), nullable=False, default="student")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )
    avatar_key = Column(String(255), nullable=True, index=True)
    # OAuth provider IDs
    google_id = Column(String(255), nullable=True, unique=True, index=True)
    # Google Calendar integration
    google_calendar_access_token = Column(Text, nullable=True)
    google_calendar_refresh_token = Column(Text, nullable=True)
    google_calendar_token_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    google_calendar_email = Column(String(255), nullable=True)
    google_calendar_connected_at = Column(TIMESTAMP(timezone=True), nullable=True)
    currency = Column(String(3), nullable=False, default="USD", server_default="USD")
    timezone = Column(String(64), nullable=False, default="UTC", server_default="UTC")
    preferred_language = Column(String(5), nullable=False, default="en", server_default="en")
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Token security: tracks when password was last changed to invalidate old tokens
    password_changed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # Fraud detection: tracks registration signals for trial abuse prevention
    registration_ip = Column(INET, nullable=True, index=True)
    trial_restricted = Column(Boolean, default=False, nullable=False)
    fraud_flags = Column(JSONB, default=list, server_default="[]")

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
    notification_preferences = relationship(
        "NotificationPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (CheckConstraint("role IN ('student', 'tutor', 'admin', 'owner')", name="valid_role"),)


class UserProfile(Base):
    """Extended user profile."""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    phone = Column(String(20))
    bio = Column(Text)
    timezone = Column(String(64), default="UTC")
    # Phase 3: struct.txt compliance fields
    country_of_birth = Column(String(2))  # ISO 3166-1 alpha-2
    phone_country_code = Column(String(5))  # E.164 format (+1 to +999)
    date_of_birth = Column(Date)  # For age verification
    age_confirmed = Column(Boolean, default=False, nullable=False)  # 18+ confirmation
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

    # Relationships
    user = relationship("User", back_populates="profile")


class RegistrationFraudSignal(Base):
    """Tracks fraud signals detected during registration for trial abuse prevention."""

    __tablename__ = "registration_fraud_signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    signal_type = Column(String(50), nullable=False)
    signal_value = Column(Text, nullable=False)
    confidence_score = Column(
        Integer,
        default=50,
        nullable=False,
    )
    detected_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_outcome = Column(String(20), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="fraud_signals")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint(
            "signal_type IN ('ip_address', 'device_fingerprint', 'email_pattern', 'browser_fingerprint', 'behavioral')",
            name="valid_signal_type",
        ),
        CheckConstraint(
            "review_outcome IS NULL OR review_outcome IN ('legitimate', 'fraudulent', 'suspicious')",
            name="valid_review_outcome",
        ),
    )
