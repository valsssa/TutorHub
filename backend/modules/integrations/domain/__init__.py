"""
Integrations domain layer.

Contains domain entities, value objects, exceptions, and repository interfaces
for third-party integrations (Google Calendar, Zoom, video meetings).
"""

from modules.integrations.domain.entities import (
    CalendarEventEntity,
    IntegrationSyncResult,
    MeetingCreationResult,
    UserIntegrationEntity,
    VideoMeetingEntity,
)
from modules.integrations.domain.exceptions import (
    CalendarSyncError,
    IntegrationAuthError,
    IntegrationConnectionError,
    IntegrationDisabledError,
    IntegrationError,
    IntegrationNotFoundError,
    OAuthFlowError,
    RateLimitError,
    TokenExpiredError,
    VideoMeetingError,
)
from modules.integrations.domain.repositories import (
    CalendarEventRepository,
    UserIntegrationRepository,
    VideoMeetingRepository,
)
from modules.integrations.domain.value_objects import (
    ACTIVE_INTEGRATION_STATUSES,
    RECONNECTABLE_STATUSES,
    TERMINAL_INTEGRATION_STATUSES,
    CalendarEventInfo,
    IntegrationConfig,
    IntegrationId,
    IntegrationStatus,
    IntegrationType,
    MeetingLink,
    OAuthCredentials,
    VideoMeetingId,
    VideoProvider,
)

__all__ = [
    # Entities
    "UserIntegrationEntity",
    "VideoMeetingEntity",
    "CalendarEventEntity",
    "IntegrationSyncResult",
    "MeetingCreationResult",
    # Value Objects
    "IntegrationId",
    "VideoMeetingId",
    "IntegrationType",
    "IntegrationStatus",
    "VideoProvider",
    "OAuthCredentials",
    "MeetingLink",
    "CalendarEventInfo",
    "IntegrationConfig",
    # Status constants
    "TERMINAL_INTEGRATION_STATUSES",
    "ACTIVE_INTEGRATION_STATUSES",
    "RECONNECTABLE_STATUSES",
    # Exceptions
    "IntegrationError",
    "IntegrationNotFoundError",
    "IntegrationAuthError",
    "IntegrationConnectionError",
    "VideoMeetingError",
    "CalendarSyncError",
    "OAuthFlowError",
    "TokenExpiredError",
    "RateLimitError",
    "IntegrationDisabledError",
    # Repository protocols
    "UserIntegrationRepository",
    "VideoMeetingRepository",
    "CalendarEventRepository",
]
