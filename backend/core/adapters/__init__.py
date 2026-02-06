"""
Adapter implementations for port interfaces.

Adapters implement the port protocols for specific technologies:
- StripeAdapter: Stripe payment processing
- BrevoAdapter: Brevo/Sendinblue email sending
- MinIOAdapter: MinIO/S3 file storage
- RedisAdapter: Redis caching and distributed locks
- ZoomAdapter: Zoom video meetings
- GoogleCalendarAdapter: Google Calendar integration
"""

from core.adapters.brevo_adapter import BrevoAdapter
from core.adapters.google_calendar_adapter import GoogleCalendarAdapter
from core.adapters.minio_adapter import MinIOAdapter
from core.adapters.redis_adapter import RedisAdapter
from core.adapters.stripe_adapter import StripeAdapter
from core.adapters.zoom_adapter import ZoomAdapter

__all__ = [
    "StripeAdapter",
    "BrevoAdapter",
    "MinIOAdapter",
    "RedisAdapter",
    "ZoomAdapter",
    "GoogleCalendarAdapter",
]
