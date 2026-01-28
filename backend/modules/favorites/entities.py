"""Favorites domain entities."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class FavoriteTutor(Base):
    """Model for student's favorite tutors."""

    __tablename__ = "favorite_tutors"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tutor_profile_id = Column(Integer, ForeignKey("tutor_profiles.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    student = relationship("User", foreign_keys=[student_id])
    tutor_profile = relationship("TutorProfile", foreign_keys=[tutor_profile_id])

    # Unique constraint to prevent duplicates
    __table_args__ = (
        {'extend_existing': True}
    )
