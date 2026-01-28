"""Subject classification models."""

from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Subject(Base):
    """Subject catalog."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(50))  # e.g., 'STEM', 'Languages', 'Arts', 'Business'
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    tutor_subjects = relationship("TutorSubject", back_populates="subject", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="subject")
