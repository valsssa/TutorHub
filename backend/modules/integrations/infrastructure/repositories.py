"""
SQLAlchemy repository implementations for integrations module.

These repositories implement the domain repository protocols using SQLAlchemy ORM.
Since the current schema stores integration data on existing tables (User for OAuth
credentials, Booking for video meetings), these repositories adapt to that structure.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from core.datetime_utils import utc_now

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Booking, User
from modules.integrations.domain.entities import (
    CalendarEventEntity,
    UserIntegrationEntity,
    VideoMeetingEntity,
)
from modules.integrations.domain.repositories import (
    CalendarEventRepository,
    UserIntegrationRepository,
    VideoMeetingRepository,
)
from modules.integrations.domain.value_objects import (
    IntegrationId,
    IntegrationStatus,
    IntegrationType,
    OAuthCredentials,
    VideoMeetingId,
    VideoProvider,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class UserIntegrationRepositoryImpl(UserIntegrationRepository):
    """
    Repository for user integrations backed by SQLAlchemy ORM.

    Currently, integrations are stored on the User model:
    - Google Calendar: google_calendar_* fields on User
    - Zoom: Not user-specific (Server-to-Server OAuth)

    This implementation abstracts those fields into UserIntegrationEntity.
    """

    db: Session

    def get_by_id(self, integration_id: IntegrationId) -> UserIntegrationEntity | None:
        """
        Get an integration by its ID.

        Since integrations are stored on User, the integration_id is the user_id
        combined with the integration type. We use a convention:
        - Google Calendar: user_id * 10 + 1

        Args:
            integration_id: Integration's unique identifier

        Returns:
            UserIntegrationEntity if found, None otherwise
        """
        user_id, integration_type = self._decode_integration_id(integration_id)
        return self.get_by_user_and_type(user_id, integration_type)

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
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return None

        if integration_type == IntegrationType.GOOGLE_CALENDAR:
            return self._user_to_google_calendar_entity(user)
        elif integration_type == IntegrationType.GOOGLE_MEET:
            # Google Meet uses the same OAuth as Google Calendar
            return self._user_to_google_calendar_entity(user)

        # Other integration types not yet implemented
        return None

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
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return []

        integrations: list[UserIntegrationEntity] = []

        # Check Google Calendar integration
        google_entity = self._user_to_google_calendar_entity(user)
        if google_entity and (status is None or google_entity.status == status):
            integrations.append(google_entity)

        return integrations

    def create(self, integration: UserIntegrationEntity) -> UserIntegrationEntity:
        """
        Create a new user integration.

        Args:
            integration: Integration entity to create

        Returns:
            Created integration with populated ID
        """
        user = (
            self.db.query(User)
            .filter(User.id == integration.user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            raise ValueError(f"User {integration.user_id} not found")

        now = utc_now()

        if integration.integration_type == IntegrationType.GOOGLE_CALENDAR:
            user.google_calendar_connected_at = integration.connected_at or now
            if integration.credentials:
                user.google_calendar_access_token = integration.credentials.access_token
                user.google_calendar_refresh_token = integration.credentials.refresh_token
                user.google_calendar_token_expires = integration.credentials.expires_at
            if integration.external_email:
                user.google_calendar_email = integration.external_email
            user.updated_at = now

            self.db.commit()
            self.db.refresh(user)

            return self._user_to_google_calendar_entity(user)  # type: ignore

        raise ValueError(f"Unsupported integration type: {integration.integration_type}")

    def update(self, integration: UserIntegrationEntity) -> UserIntegrationEntity:
        """
        Update an existing integration.

        Args:
            integration: Integration entity with updated fields

        Returns:
            Updated integration entity
        """
        user = (
            self.db.query(User)
            .filter(User.id == integration.user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            raise ValueError(f"User {integration.user_id} not found")

        now = utc_now()

        if integration.integration_type == IntegrationType.GOOGLE_CALENDAR:
            if integration.credentials:
                user.google_calendar_access_token = integration.credentials.access_token
                user.google_calendar_refresh_token = integration.credentials.refresh_token
                user.google_calendar_token_expires = integration.credentials.expires_at
            if integration.external_email:
                user.google_calendar_email = integration.external_email
            if integration.connected_at:
                user.google_calendar_connected_at = integration.connected_at
            if integration.status == IntegrationStatus.DISCONNECTED:
                user.google_calendar_access_token = None
                user.google_calendar_refresh_token = None
                user.google_calendar_token_expires = None
            user.updated_at = now

            self.db.commit()
            self.db.refresh(user)

            return self._user_to_google_calendar_entity(user)  # type: ignore

        raise ValueError(f"Unsupported integration type: {integration.integration_type}")

    def delete(self, integration_id: IntegrationId) -> bool:
        """
        Delete an integration.

        Args:
            integration_id: Integration ID to delete

        Returns:
            True if deleted, False if not found
        """
        user_id, integration_type = self._decode_integration_id(integration_id)

        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.deleted_at.is_(None))
            .first()
        )
        if not user:
            return False

        now = utc_now()

        if integration_type == IntegrationType.GOOGLE_CALENDAR:
            if not user.google_calendar_refresh_token:
                return False

            user.google_calendar_access_token = None
            user.google_calendar_refresh_token = None
            user.google_calendar_token_expires = None
            user.google_calendar_email = None
            user.google_calendar_connected_at = None
            user.updated_at = now

            self.db.commit()
            return True

        return False

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
        offset = (page - 1) * page_size

        if integration_type == IntegrationType.GOOGLE_CALENDAR:
            users = (
                self.db.query(User)
                .filter(
                    User.deleted_at.is_(None),
                    User.google_calendar_refresh_token.isnot(None),
                )
                .offset(offset)
                .limit(page_size)
                .all()
            )
            return [
                entity
                for user in users
                if (entity := self._user_to_google_calendar_entity(user)) is not None
            ]

        return []

    def get_errored_integrations(
        self,
        *,
        max_error_count: int | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> list[UserIntegrationEntity]:
        """
        Get integrations in error state.

        Currently, we don't track error state in the database.
        This would require additional columns on User.

        Args:
            max_error_count: Only return if error count is below this
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of errored integrations (empty for now)
        """
        # Error tracking not implemented in current schema
        # Would need additional columns: google_calendar_error_count, google_calendar_last_error, etc.
        logger.warning("get_errored_integrations not fully implemented - no error tracking columns")
        return []

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
        if integration_type == IntegrationType.GOOGLE_CALENDAR:
            query = self.db.query(func.count(User.id)).filter(User.deleted_at.is_(None))

            if status == IntegrationStatus.CONNECTED:
                query = query.filter(User.google_calendar_refresh_token.isnot(None))
            elif status == IntegrationStatus.DISCONNECTED:
                query = query.filter(User.google_calendar_refresh_token.is_(None))

            return query.scalar() or 0

        return 0

    def _user_to_google_calendar_entity(self, user: User) -> UserIntegrationEntity | None:
        """
        Convert User model's Google Calendar fields to UserIntegrationEntity.

        Args:
            user: User SQLAlchemy model

        Returns:
            UserIntegrationEntity or None if not connected
        """
        # If no refresh token, integration is disconnected or never connected
        if not user.google_calendar_refresh_token:
            return None

        credentials = OAuthCredentials(
            access_token=user.google_calendar_access_token or "",
            refresh_token=user.google_calendar_refresh_token,
            expires_at=user.google_calendar_token_expires,
        )

        # Determine status based on token state
        status = IntegrationStatus.CONNECTED
        if credentials.is_expired and not credentials.can_refresh:
            status = IntegrationStatus.ERROR

        integration_id = self._encode_integration_id(
            user.id, IntegrationType.GOOGLE_CALENDAR
        )

        return UserIntegrationEntity(
            id=integration_id,
            user_id=user.id,
            integration_type=IntegrationType.GOOGLE_CALENDAR,
            status=status,
            credentials=credentials,
            external_email=user.google_calendar_email,
            connected_at=user.google_calendar_connected_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def _encode_integration_id(
        self, user_id: int, integration_type: IntegrationType
    ) -> IntegrationId:
        """
        Encode user_id and integration_type into a single integration_id.

        Convention: user_id * 10 + type_code
        - GOOGLE_CALENDAR: 1
        - ZOOM: 2
        - GOOGLE_MEET: 3
        - MICROSOFT_TEAMS: 4
        - CUSTOM_VIDEO: 5
        """
        type_codes = {
            IntegrationType.GOOGLE_CALENDAR: 1,
            IntegrationType.ZOOM: 2,
            IntegrationType.GOOGLE_MEET: 3,
            IntegrationType.MICROSOFT_TEAMS: 4,
            IntegrationType.CUSTOM_VIDEO: 5,
        }
        return IntegrationId(user_id * 10 + type_codes.get(integration_type, 0))

    def _decode_integration_id(
        self, integration_id: IntegrationId
    ) -> tuple[int, IntegrationType]:
        """
        Decode integration_id back to user_id and integration_type.
        """
        type_codes = {
            1: IntegrationType.GOOGLE_CALENDAR,
            2: IntegrationType.ZOOM,
            3: IntegrationType.GOOGLE_MEET,
            4: IntegrationType.MICROSOFT_TEAMS,
            5: IntegrationType.CUSTOM_VIDEO,
        }
        user_id = integration_id // 10
        type_code = integration_id % 10
        return user_id, type_codes.get(type_code, IntegrationType.GOOGLE_CALENDAR)


@dataclass(slots=True)
class VideoMeetingRepositoryImpl(VideoMeetingRepository):
    """
    Repository for video meetings backed by SQLAlchemy ORM.

    Video meeting data is stored on the Booking model:
    - zoom_meeting_id: Zoom meeting ID
    - join_url / meeting_url: Meeting join URL
    - video_provider: Provider type (zoom, google_meet, etc.)
    - google_meet_link: Google Meet specific link

    This implementation abstracts those fields into VideoMeetingEntity.
    """

    db: Session

    def get_by_id(self, meeting_id: VideoMeetingId) -> VideoMeetingEntity | None:
        """
        Get a meeting by its ID.

        Since meetings are stored on Booking, meeting_id equals booking_id.

        Args:
            meeting_id: Meeting's unique identifier (same as booking_id)

        Returns:
            VideoMeetingEntity if found, None otherwise
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == meeting_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            return None
        return self._booking_to_entity(booking)

    def get_by_booking(self, booking_id: int) -> VideoMeetingEntity | None:
        """
        Get the meeting for a specific booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            VideoMeetingEntity if found, None otherwise
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            return None
        return self._booking_to_entity(booking)

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
        booking = None

        if provider == VideoProvider.ZOOM:
            booking = (
                self.db.query(Booking)
                .filter(
                    Booking.zoom_meeting_id == external_meeting_id,
                    Booking.deleted_at.is_(None),
                )
                .first()
            )
        elif provider == VideoProvider.GOOGLE_MEET:
            # Google Meet links contain meeting codes, search by link pattern
            booking = (
                self.db.query(Booking)
                .filter(
                    Booking.google_meet_link.contains(external_meeting_id),
                    Booking.deleted_at.is_(None),
                )
                .first()
            )

        if not booking:
            return None
        return self._booking_to_entity(booking)

    def create(self, meeting: VideoMeetingEntity) -> VideoMeetingEntity:
        """
        Create a new video meeting record.

        This updates the Booking record with meeting information.

        Args:
            meeting: Meeting entity to create

        Returns:
            Created meeting with populated ID
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == meeting.booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            raise ValueError(f"Booking {meeting.booking_id} not found")

        now = utc_now()

        booking.video_provider = meeting.provider.value
        booking.meeting_url = meeting.meeting_url
        booking.join_url = meeting.meeting_url

        if meeting.provider == VideoProvider.ZOOM:
            booking.zoom_meeting_id = meeting.meeting_id
        elif meeting.provider == VideoProvider.GOOGLE_MEET:
            booking.google_meet_link = meeting.meeting_url

        booking.updated_at = now

        self.db.commit()
        self.db.refresh(booking)

        return self._booking_to_entity(booking)  # type: ignore

    def update(self, meeting: VideoMeetingEntity) -> VideoMeetingEntity:
        """
        Update an existing meeting.

        Args:
            meeting: Meeting entity with updated fields

        Returns:
            Updated meeting entity
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == meeting.booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            raise ValueError(f"Booking {meeting.booking_id} not found")

        now = utc_now()

        booking.video_provider = meeting.provider.value
        booking.meeting_url = meeting.meeting_url
        booking.join_url = meeting.meeting_url

        if meeting.provider == VideoProvider.ZOOM:
            booking.zoom_meeting_id = meeting.meeting_id
        elif meeting.provider == VideoProvider.GOOGLE_MEET:
            booking.google_meet_link = meeting.meeting_url

        # Handle deactivation
        if not meeting.is_active:
            booking.meeting_url = None
            booking.join_url = None

        booking.updated_at = now

        self.db.commit()
        self.db.refresh(booking)

        return self._booking_to_entity(booking)  # type: ignore

    def delete(self, meeting_id: VideoMeetingId) -> bool:
        """
        Delete a meeting record.

        Clears meeting data from the Booking.

        Args:
            meeting_id: Meeting ID to delete

        Returns:
            True if deleted, False if not found
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == meeting_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            return False

        if not booking.meeting_url and not booking.zoom_meeting_id:
            return False

        now = utc_now()

        booking.video_provider = None
        booking.meeting_url = None
        booking.join_url = None
        booking.zoom_meeting_id = None
        booking.google_meet_link = None
        booking.updated_at = now

        self.db.commit()
        return True

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
        offset = (page - 1) * page_size

        query = (
            self.db.query(Booking)
            .filter(
                Booking.deleted_at.is_(None),
                Booking.video_provider == provider.value,
                Booking.meeting_url.isnot(None),
            )
        )

        # Filter for active sessions (SCHEDULED or ACTIVE)
        query = query.filter(Booking.session_state.in_(["SCHEDULED", "ACTIVE"]))

        bookings = query.offset(offset).limit(page_size).all()

        return [
            entity
            for booking in bookings
            if (entity := self._booking_to_entity(booking)) is not None
        ]

    def get_expired_meetings(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[VideoMeetingEntity]:
        """
        Get meetings that have expired.

        A meeting is expired if the booking has ended (past end_time).

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of expired meetings
        """
        offset = (page - 1) * page_size
        now = utc_now()

        bookings = (
            self.db.query(Booking)
            .filter(
                Booking.deleted_at.is_(None),
                Booking.meeting_url.isnot(None),
                Booking.end_time < now,
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [
            entity
            for booking in bookings
            if (entity := self._booking_to_entity(booking)) is not None
        ]

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
        query = (
            self.db.query(func.count(Booking.id))
            .filter(
                Booking.deleted_at.is_(None),
                Booking.video_provider == provider.value,
                Booking.meeting_url.isnot(None),
            )
        )

        if is_active is True:
            query = query.filter(Booking.session_state.in_(["SCHEDULED", "ACTIVE"]))
        elif is_active is False:
            query = query.filter(
                Booking.session_state.in_(["ENDED", "CANCELLED", "EXPIRED"])
            )

        return query.scalar() or 0

    def _booking_to_entity(self, booking: Booking) -> VideoMeetingEntity | None:
        """
        Convert Booking model's meeting fields to VideoMeetingEntity.

        Args:
            booking: Booking SQLAlchemy model

        Returns:
            VideoMeetingEntity or None if no meeting attached
        """
        # If no meeting URL or meeting ID, no meeting exists
        meeting_url = booking.meeting_url or booking.join_url or booking.google_meet_link
        if not meeting_url and not booking.zoom_meeting_id:
            return None

        # Determine provider
        provider = VideoProvider.ZOOM  # Default
        if booking.video_provider:
            try:
                provider = VideoProvider(booking.video_provider)
            except ValueError:
                logger.warning(
                    "Unknown video provider '%s' for booking %d",
                    booking.video_provider,
                    booking.id,
                )

        # Use booking end_time as expiration
        expires_at = booking.end_time

        # Determine if active based on session state
        is_active = booking.session_state in ["SCHEDULED", "ACTIVE"]

        return VideoMeetingEntity(
            id=VideoMeetingId(booking.id),
            booking_id=booking.id,
            provider=provider,
            meeting_url=meeting_url or "",
            meeting_id=booking.zoom_meeting_id,
            host_url=None,  # Not stored in current schema
            password=None,  # Not stored in current schema
            provider_response={},  # Not stored in current schema
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            expires_at=expires_at,
            is_active=is_active,
            last_accessed_at=None,  # Not tracked in current schema
        )


@dataclass(slots=True)
class CalendarEventRepositoryImpl(CalendarEventRepository):
    """
    Repository for calendar events backed by SQLAlchemy ORM.

    Calendar event data is stored on the Booking model:
    - google_calendar_event_id: External calendar event ID

    This implementation abstracts those fields into CalendarEventEntity.
    Note: This is a simplified implementation as the current schema only
    stores the event ID on the Booking, not full event details.
    """

    db: Session

    def get_by_id(self, event_id: int) -> CalendarEventEntity | None:
        """
        Get a calendar event by its ID.

        Since events are stored on Booking, event_id equals booking_id.

        Args:
            event_id: Event's unique identifier (same as booking_id)

        Returns:
            CalendarEventEntity if found, None otherwise
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == event_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking or not booking.google_calendar_event_id:
            return None
        return self._booking_to_calendar_entity(booking, event_id)

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
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking or not booking.google_calendar_event_id:
            return None

        # In the current schema, we only store tutor's calendar event
        # Check if user is the tutor
        if booking.tutor_profile and booking.tutor_profile.user_id == user_id:
            return self._booking_to_calendar_entity(booking, user_id)

        return None

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
        booking = (
            self.db.query(Booking)
            .filter(
                Booking.google_calendar_event_id == external_event_id,
                Booking.deleted_at.is_(None),
            )
            .first()
        )
        if not booking:
            return None

        # Decode integration_id to get user_id
        user_id = integration_id // 10
        return self._booking_to_calendar_entity(booking, user_id)

    def get_all_for_booking(self, booking_id: int) -> list[CalendarEventEntity]:
        """
        Get all calendar events for a booking.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            List of calendar events
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking or not booking.google_calendar_event_id:
            return []

        # In current schema, we only have tutor's calendar event
        if booking.tutor_profile:
            entity = self._booking_to_calendar_entity(
                booking, booking.tutor_profile.user_id
            )
            if entity:
                return [entity]

        return []

    def create(self, event: CalendarEventEntity) -> CalendarEventEntity:
        """
        Create a new calendar event record.

        Args:
            event: Event entity to create

        Returns:
            Created event with populated ID
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == event.booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            raise ValueError(f"Booking {event.booking_id} not found")

        now = utc_now()

        booking.google_calendar_event_id = event.external_event_id
        booking.updated_at = now

        self.db.commit()
        self.db.refresh(booking)

        return CalendarEventEntity(
            id=booking.id,
            booking_id=booking.id,
            user_id=event.user_id,
            integration_id=event.integration_id,
            external_event_id=event.external_event_id,
            calendar_id=event.calendar_id,
            title=event.title,
            html_link=event.html_link,
            created_at=booking.created_at,
            updated_at=now,
            synced_at=now,
            is_synced=True,
        )

    def update(self, event: CalendarEventEntity) -> CalendarEventEntity:
        """
        Update an existing calendar event.

        Args:
            event: Event entity with updated fields

        Returns:
            Updated event entity
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == event.booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            raise ValueError(f"Booking {event.booking_id} not found")

        now = utc_now()

        booking.google_calendar_event_id = event.external_event_id
        booking.updated_at = now

        self.db.commit()
        self.db.refresh(booking)

        return CalendarEventEntity(
            id=booking.id,
            booking_id=booking.id,
            user_id=event.user_id,
            integration_id=event.integration_id,
            external_event_id=event.external_event_id,
            calendar_id=event.calendar_id,
            title=event.title,
            html_link=event.html_link,
            created_at=event.created_at,
            updated_at=now,
            synced_at=event.synced_at,
            is_synced=event.is_synced,
            sync_error=event.sync_error,
        )

    def delete(self, event_id: int) -> bool:
        """
        Delete a calendar event record.

        Args:
            event_id: Event ID to delete

        Returns:
            True if deleted, False if not found
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == event_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking or not booking.google_calendar_event_id:
            return False

        now = utc_now()

        booking.google_calendar_event_id = None
        booking.updated_at = now

        self.db.commit()
        return True

    def get_unsynced_events(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[CalendarEventEntity]:
        """
        Get calendar events that need syncing.

        Currently not fully implemented as sync status is not tracked.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of unsynced events
        """
        # Sync status not tracked in current schema
        logger.warning("get_unsynced_events not fully implemented - no sync tracking")
        return []

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
        from models import TutorProfile

        user_id = integration_id // 10
        offset = (page - 1) * page_size

        # Find tutor profile for user
        tutor_profile = (
            self.db.query(TutorProfile)
            .filter(TutorProfile.user_id == user_id, TutorProfile.deleted_at.is_(None))
            .first()
        )
        if not tutor_profile:
            return []

        bookings = (
            self.db.query(Booking)
            .filter(
                Booking.tutor_profile_id == tutor_profile.id,
                Booking.google_calendar_event_id.isnot(None),
                Booking.deleted_at.is_(None),
            )
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return [
            entity
            for booking in bookings
            if (entity := self._booking_to_calendar_entity(booking, user_id)) is not None
        ]

    def _booking_to_calendar_entity(
        self, booking: Booking, user_id: int
    ) -> CalendarEventEntity | None:
        """
        Convert Booking model's calendar fields to CalendarEventEntity.

        Args:
            booking: Booking SQLAlchemy model
            user_id: User ID for the integration

        Returns:
            CalendarEventEntity or None if no event attached
        """
        if not booking.google_calendar_event_id:
            return None

        # Build integration ID
        integration_id = IntegrationId(user_id * 10 + 1)  # 1 = GOOGLE_CALENDAR

        return CalendarEventEntity(
            id=booking.id,
            booking_id=booking.id,
            user_id=user_id,
            integration_id=integration_id,
            external_event_id=booking.google_calendar_event_id,
            calendar_id="primary",
            title=booking.subject_name or "Tutoring Session",
            html_link=None,  # Not stored in current schema
            created_at=booking.created_at,
            updated_at=booking.updated_at,
            synced_at=booking.updated_at,  # Approximate
            is_synced=True,  # Assume synced if event ID exists
        )
