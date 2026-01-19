"""Student-related models."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DECIMAL,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


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
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now()
        # No onupdate - updated_at is set in application code
    )

    # Relationships
    user = relationship("User", back_populates="student_profile")




class FavoriteTutor(Base):
    """Student favorite tutors."""

    __tablename__ = "favorite_tutors"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    tutor_profile_id = Column(
        Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE")
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    tutor_profile = relationship("TutorProfile", back_populates="favorites")




class StudentPackage(Base):
    """Student-purchased packages and subscriptions."""

    __tablename__ = "student_packages"

    id = Column(Integer, primary_key=True)
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tutor_profile_id = Column(
        Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False
    )
    pricing_option_id = Column(
        Integer,
        ForeignKey("tutor_pricing_options.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sessions_purchased = Column(Integer, nullable=False)
    sessions_remaining = Column(Integer, nullable=False)
    sessions_used = Column(Integer, default=0, nullable=False)
    purchase_price = Column(DECIMAL(10, 2), nullable=False)
    purchased_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    payment_intent_id = Column(String(255), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        # No onupdate - updated_at is set in application code
        nullable=False,
    )

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    tutor_profile = relationship(
        "TutorProfile", foreign_keys="StudentPackage.tutor_profile_id"
    )
    pricing_option = relationship(
        "TutorPricingOption", foreign_keys="StudentPackage.pricing_option_id"
    )

    __table_args__ = (
        CheckConstraint("sessions_purchased > 0", name="positive_sessions_purchased"),
        CheckConstraint(
            "sessions_remaining >= 0", name="non_negative_sessions_remaining"
        ),
        CheckConstraint("sessions_used >= 0", name="non_negative_sessions_used"),
        CheckConstraint("purchase_price > 0", name="positive_purchase_price"),
        CheckConstraint(
            "status IN ('active', 'expired', 'exhausted', 'refunded')",
            name="valid_package_status",
        ),
    )


