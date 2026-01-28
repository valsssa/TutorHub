"""Admin and audit models."""

from sqlalchemy import (
    TIMESTAMP,
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
