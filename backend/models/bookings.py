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

from .base import Base


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
    join_url = Column(Text)  # Meeting URL for virtual sessions
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
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
    )

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
