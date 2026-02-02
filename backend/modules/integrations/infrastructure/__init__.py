"""
Infrastructure implementations for integrations module.

Provides SQLAlchemy-based repository implementations for:
- UserIntegrationRepository: OAuth credentials for third-party services
- VideoMeetingRepository: Video meeting data attached to bookings
- CalendarEventRepository: Calendar events synced with bookings
"""

from modules.integrations.infrastructure.repositories import (
    CalendarEventRepositoryImpl,
    UserIntegrationRepositoryImpl,
    VideoMeetingRepositoryImpl,
)

__all__ = [
    "UserIntegrationRepositoryImpl",
    "VideoMeetingRepositoryImpl",
    "CalendarEventRepositoryImpl",
]
