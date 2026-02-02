"""
Fake implementations for testing.

These in-memory implementations of port interfaces are used in tests
to avoid dependencies on external services.
"""

from core.fakes.fake_cache import FakeCache
from core.fakes.fake_calendar import FakeCalendar
from core.fakes.fake_email import FakeEmail
from core.fakes.fake_meeting import FakeMeeting
from core.fakes.fake_payment import FakePayment
from core.fakes.fake_storage import FakeStorage

__all__ = [
    "FakePayment",
    "FakeEmail",
    "FakeStorage",
    "FakeCache",
    "FakeMeeting",
    "FakeCalendar",
]
