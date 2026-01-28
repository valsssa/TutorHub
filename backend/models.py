"""
DEPRECATED: This file is maintained for backward compatibility only.

All models have been split into domain-specific files in the models/ package.

New code should import from models.* instead:
    from models.auth import User
    from models.tutors import TutorProfile
    from models.bookings import Booking

This file will be removed in a future version.
"""

# Re-export all models from the new modular structure
from models import *  # noqa: F401, F403

# Explicitly list all exports for IDE autocomplete
from models import (  # noqa: F401
    AuditLog,
    Base,
    Booking,
    FavoriteTutor,
    JSONEncodedArray,
    Message,
    Notification,
    Payment,
    Payout,
    Refund,
    Report,
    Review,
    SessionMaterial,
    StudentPackage,
    StudentProfile,
    Subject,
    SupportedCurrency,
    TutorAvailability,
    TutorBlackout,
    TutorCertification,
    TutorEducation,
    TutorPricingOption,
    TutorProfile,
    TutorSubject,
    User,
    UserProfile,
)
