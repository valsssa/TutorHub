"""
Domain-driven models package.

This package organizes SQLAlchemy models by domain for better maintainability.
All models are re-exported here for backward compatibility with existing imports.

Usage:
    # Preferred (explicit domain imports)
    from models.auth import User
    from models.tutors import TutorProfile
    from models.bookings import Booking

    # Still works (backward compatible)
    from models import User, TutorProfile, Booking
"""

# Import domain modules first to ensure all models are loaded
from . import admin, auth, bookings, messages, notifications, payments, reviews, students, subjects, tutors
from .base import Base, JSONEncodedArray

# Re-export all models for backward compatibility
from .admin import AuditLog, Report
from .auth import User, UserProfile
from .bookings import Booking, SessionMaterial
from .messages import Message, MessageAttachment
from .notifications import Notification
from .payments import Payment, Payout, Refund, SupportedCurrency
from .reviews import Review
from .students import FavoriteTutor, StudentPackage, StudentProfile
from .subjects import Subject
from .tutors import (
    TutorAvailability,
    TutorBlackout,
    TutorCertification,
    TutorEducation,
    TutorPricingOption,
    TutorProfile,
    TutorSubject,
)

__all__ = [
    # Base
    "Base",
    "JSONEncodedArray",
    # Auth
    "User",
    "UserProfile",
    # Tutors
    "TutorProfile",
    "TutorSubject",
    "TutorCertification",
    "TutorEducation",
    "TutorPricingOption",
    "TutorAvailability",
    "TutorBlackout",
    # Students
    "StudentProfile",
    "StudentPackage",
    "FavoriteTutor",
    # Bookings
    "Booking",
    "SessionMaterial",
    # Subjects
    "Subject",
    # Reviews
    "Review",
    # Messages
    "Message",
    "MessageAttachment",
    # Notifications
    "Notification",
    # Payments
    "Payment",
    "Refund",
    "Payout",
    "SupportedCurrency",
    # Admin
    "Report",
    "AuditLog",
]
