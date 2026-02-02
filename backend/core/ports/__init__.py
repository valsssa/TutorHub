"""
Port interfaces for clean architecture.

Ports define the contracts (interfaces) that the application core uses
to interact with external services. Adapters implement these ports for
specific technologies (Stripe, Brevo, MinIO, Redis, etc.).

This allows:
- Swapping implementations without changing business logic
- Easy testing with fake/mock implementations
- Clear separation of concerns
"""

from core.ports.cache import CachePort, LockResult
from core.ports.calendar import CalendarPort, CalendarResult, FreeBusyResult
from core.ports.email import EmailPort, EmailResult
from core.ports.meeting import MeetingPort, MeetingResult
from core.ports.payment import PaymentPort, PaymentResult
from core.ports.storage import StoragePort, StorageResult

__all__ = [
    # Payment
    "PaymentPort",
    "PaymentResult",
    # Email
    "EmailPort",
    "EmailResult",
    # Storage
    "StoragePort",
    "StorageResult",
    # Cache
    "CachePort",
    "LockResult",
    # Meeting
    "MeetingPort",
    "MeetingResult",
    # Calendar
    "CalendarPort",
    "CalendarResult",
    "FreeBusyResult",
]
