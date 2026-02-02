"""
Repository interfaces for integrations module.

Defines the contracts for integration persistence operations.
"""

from typing import Protocol

from modules.integrations.domain.entities import (
    CalendarEventEntity,
    UserIntegrationEntity,
    VideoMeetingEntity,
)
from modules.integrations.domain.value_objects import (
    IntegrationId,
    IntegrationStatus,
    IntegrationType,
    VideoMeetingId,
    VideoProvider,
)


class UserIntegrationRepository(Protocol):
    """
    Protocol for user integration repository operations.

    Implementations should handle:
    - Integration CRUD operations
    - User-specific lookups
    - Status-based queries
    """

    def get_by_id(self, integration_id: IntegrationId) -> UserIntegrationEntity | None:
        """
        Get an integration by its ID.

        Args:
            integration_id: Integration's unique identifier

        Returns:
            UserIntegrationEntity if found, None otherwise
        """
        ...

    def get_by_user_and_type(
        self,
        user_id: int,
        integration_type: IntegrationType,
    ) -> UserIntegrationEntity | None:
        """
        Get a specific integration for a user.

        Args:
            user_id: User's unique identifier
            integration_type: Type of integration

        Returns:
            UserIntegrationEntity if found, None otherwise
        """
        ...

    def get_all_for_user(
        self,
        user_id: int,
        *,
        status: IntegrationStatus | None = None,
    ) -> list[UserIntegrationEntity]:
        """
        Get all integrations for a user.

        Args:
            user_id: User's unique identifier
            status: Optional filter by status

        Returns:
            List of user's integrations
        """
        ...

    def create(self, integration: UserIntegrationEntity) -> UserIntegrationEntity:
        """
        Create a new user integration.

        Args:
            integration: Integration entity to create

        Returns:
            Created integration with populated ID
        """
        ...

    def update(self, integration: UserIntegrationEntity) -> UserIntegrationEntity:
        """
        Update an existing integration.

        Args:
            integration: Integration entity with updated fields

        Returns:
            Updated integration entity
        """
        ...

    def delete(self, integration_id: IntegrationId) -> bool:
        """
        Delete an integration.

        Args:
            integration_id: Integration ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def get_connected_by_type(
        self,
        integration_type: IntegrationType,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[UserIntegrationEntity]:
        """
        Get all connected integrations of a specific type.

        Args:
            integration_type: Type of integration
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of connected integrations
        """
        ...

    def get_errored_integrations(
        self,
        *,
        max_error_count: int | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> list[UserIntegrationEntity]:
        """
        Get integrations in error state.

        Args:
            max_error_count: Only return if error count is below this
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of errored integrations
        """
        ...

    def count_by_type(
        self,
        integration_type: IntegrationType,
        *,
        status: IntegrationStatus | None = None,
    ) -> int:
        """
        Count integrations of a specific type.

        Args:
            integration_type: Type of integration
            status: Optional filter by status

        Returns:
            Count of matching integrations
        """
        ...


class VideoMeetingRepository(Protocol):
    """
    Protocol for video meeting repository operations.

    Implementations should handle:
    - Meeting CRUD operations
    - Booking-based lookups
    - Provider-specific queries
    """

    def get_by_id(self, meeting_id: VideoMeetingId) -> VideoMeetingEntity | None:
        """
        Get a meeting by its ID.

        Args:
            meeting_id: Meeting's unique identifier

        Returns:
            VideoMeetingEntity if found, None otherwise
        """
        ...

    def get_by_booking(self, booking_id: int) -> VideoMeetingEntity | None:
        """
        Get the meeting for a specific booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            VideoMeetingEntity if found, None otherwise
        """
        ...

    def get_by_external_id(
        self,
        provider: VideoProvider,
        external_meeting_id: str,
    ) -> VideoMeetingEntity | None:
        """
        Get a meeting by its provider-specific ID.

        Args:
            provider: Video provider
            external_meeting_id: Provider's meeting ID

        Returns:
            VideoMeetingEntity if found, None otherwise
        """
        ...

    def create(self, meeting: VideoMeetingEntity) -> VideoMeetingEntity:
        """
        Create a new video meeting record.

        Args:
            meeting: Meeting entity to create

        Returns:
            Created meeting with populated ID
        """
        ...

    def update(self, meeting: VideoMeetingEntity) -> VideoMeetingEntity:
        """
        Update an existing meeting.

        Args:
            meeting: Meeting entity with updated fields

        Returns:
            Updated meeting entity
        """
        ...

    def delete(self, meeting_id: VideoMeetingId) -> bool:
        """
        Delete a meeting record.

        Args:
            meeting_id: Meeting ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def get_active_by_provider(
        self,
        provider: VideoProvider,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[VideoMeetingEntity]:
        """
        Get all active meetings for a provider.

        Args:
            provider: Video provider
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of active meetings
        """
        ...

    def get_expired_meetings(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[VideoMeetingEntity]:
        """
        Get meetings that have expired.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of expired meetings
        """
        ...

    def count_by_provider(
        self,
        provider: VideoProvider,
        *,
        is_active: bool | None = None,
    ) -> int:
        """
        Count meetings by provider.

        Args:
            provider: Video provider
            is_active: Optional filter by active status

        Returns:
            Count of matching meetings
        """
        ...


class CalendarEventRepository(Protocol):
    """
    Protocol for calendar event repository operations.

    Implementations should handle:
    - Calendar event CRUD operations
    - Booking-based lookups
    - Sync status tracking
    """

    def get_by_id(self, event_id: int) -> CalendarEventEntity | None:
        """
        Get a calendar event by its ID.

        Args:
            event_id: Event's unique identifier

        Returns:
            CalendarEventEntity if found, None otherwise
        """
        ...

    def get_by_booking_and_user(
        self,
        booking_id: int,
        user_id: int,
    ) -> CalendarEventEntity | None:
        """
        Get the calendar event for a booking and user.

        Args:
            booking_id: Booking's unique identifier
            user_id: User's unique identifier

        Returns:
            CalendarEventEntity if found, None otherwise
        """
        ...

    def get_by_external_id(
        self,
        external_event_id: str,
        integration_id: IntegrationId,
    ) -> CalendarEventEntity | None:
        """
        Get a calendar event by its external ID.

        Args:
            external_event_id: Provider's event ID
            integration_id: Integration used to create the event

        Returns:
            CalendarEventEntity if found, None otherwise
        """
        ...

    def get_all_for_booking(self, booking_id: int) -> list[CalendarEventEntity]:
        """
        Get all calendar events for a booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            List of calendar events
        """
        ...

    def create(self, event: CalendarEventEntity) -> CalendarEventEntity:
        """
        Create a new calendar event record.

        Args:
            event: Event entity to create

        Returns:
            Created event with populated ID
        """
        ...

    def update(self, event: CalendarEventEntity) -> CalendarEventEntity:
        """
        Update an existing calendar event.

        Args:
            event: Event entity with updated fields

        Returns:
            Updated event entity
        """
        ...

    def delete(self, event_id: int) -> bool:
        """
        Delete a calendar event record.

        Args:
            event_id: Event ID to delete

        Returns:
            True if deleted, False if not found
        """
        ...

    def get_unsynced_events(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[CalendarEventEntity]:
        """
        Get calendar events that need syncing.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of unsynced events
        """
        ...

    def get_events_for_integration(
        self,
        integration_id: IntegrationId,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[CalendarEventEntity]:
        """
        Get all calendar events for an integration.

        Args:
            integration_id: Integration's unique identifier
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of calendar events
        """
        ...
