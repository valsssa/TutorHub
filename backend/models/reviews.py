"""Review and rating models."""

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base, JSONType


class Review(Base):
    """Tutor reviews and ratings."""

    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), unique=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="SET NULL"))
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    is_public = Column(Boolean, default=True)
    booking_snapshot = Column(JSONType, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="review")
    tutor_profile = relationship("TutorProfile", back_populates="reviews")
    student = relationship("User", foreign_keys=[student_id])

    __table_args__ = (CheckConstraint("rating BETWEEN 1 AND 5", name="valid_rating_value"),)

    @property
    def student_name(self) -> str | None:
        """Return the student's display name from the related User."""
        if self.student is None:
            return None
        first = self.student.first_name or ""
        last = self.student.last_name or ""
        full_name = f"{first} {last}".strip()
        return full_name if full_name else None
