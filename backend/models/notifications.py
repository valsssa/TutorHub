"""Notification models."""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Notification(Base):
    """User notifications with full feature support."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(500))
    is_read = Column(Boolean, default=False, nullable=False)
    category = Column(String(50), default="general")
    priority = Column(Integer, default=3)
    action_url = Column(String(500))
    action_label = Column(String(100))
    scheduled_for = Column(TIMESTAMP(timezone=True))
    sent_at = Column(TIMESTAMP(timezone=True))
    read_at = Column(TIMESTAMP(timezone=True))
    dismissed_at = Column(TIMESTAMP(timezone=True))
    metadata = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (CheckConstraint("priority BETWEEN 1 AND 5", name="notification_priority_check"),)

    # Relationships
    user = relationship("User", back_populates="notifications")


class NotificationPreferences(Base):
    """User notification preferences."""

    __tablename__ = "user_notification_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)

    # Type preferences
    session_reminders_enabled = Column(Boolean, default=True)
    booking_requests_enabled = Column(Boolean, default=True)
    learning_nudges_enabled = Column(Boolean, default=True)
    review_prompts_enabled = Column(Boolean, default=True)
    achievements_enabled = Column(Boolean, default=True)
    marketing_enabled = Column(Boolean, default=False)

    # Quiet hours
    quiet_hours_start = Column(Time)
    quiet_hours_end = Column(Time)
    preferred_notification_time = Column(Time)

    # Limits
    max_daily_notifications = Column(Integer, default=10)
    max_weekly_nudges = Column(Integer, default=3)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class NotificationAnalytics(Base):
    """Notification analytics for tracking engagement."""

    __tablename__ = "notification_analytics"

    id = Column(Integer, primary_key=True)
    template_key = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    sent_at = Column(TIMESTAMP(timezone=True), nullable=False)
    opened_at = Column(TIMESTAMP(timezone=True))
    clicked_at = Column(TIMESTAMP(timezone=True))
    dismissed_at = Column(TIMESTAMP(timezone=True))
    delivery_channel = Column(String(20))
    was_actionable = Column(Boolean, default=False)
    action_taken = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User")
