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
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    """User authentication model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
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
