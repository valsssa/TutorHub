"""
Repository interface for bookings module.

Defines the contract for booking persistence operations.
"""

from datetime import datetime
from typing import Protocol

from modules.bookings.domain.entities import BookingEntity
from modules.bookings.domain.status import SessionState


class BookingRepository(Protocol):
    """
    Protocol for booking repository operations.

    Implementations should handle:
    - Booking CRUD operations
    - Status-based queries
    - Optimistic locking
    """

    def get_by_id(self, booking_id: int) -> BookingEntity | None:
        """
        Get a booking by its ID.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            BookingEntity if found, None otherwise
        """
        ...

    def get_by_student(
        self,
        student_id: int,
        *,
        states: list[SessionState] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[BookingEntity]:
        """
        Get bookings for a student with optional filtering.

        Args:
            student_id: Student's user ID
            states: Filter by session states
            from_date: Filter by start date
            to_date: Filter by end date
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching bookings
        """
        ...

    def get_by_tutor(
        self,
        tutor_id: int,
        *,
        states: list[SessionState] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[BookingEntity]:
        """
        Get bookings for a tutor with optional filtering.

        Args:
            tutor_id: Tutor's user ID
            states: Filter by session states
            from_date: Filter by start date
            to_date: Filter by end date
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            List of matching bookings
        """
        ...

    def create(self, booking: BookingEntity) -> BookingEntity:
        """
        Create a new booking.

        Args:
            booking: Booking entity to create

        Returns:
            Created booking with populated ID
        """
        ...

    def update(self, booking: BookingEntity) -> BookingEntity:
        """
        Update an existing booking with optimistic locking.

        Args:
            booking: Booking entity with updated fields

        Returns:
            Updated booking entity with incremented version

        Raises:
            OptimisticLockError: If version mismatch detected
        """
        ...

    def get_pending_confirmations(
        self,
        *,
        older_than_hours: int = 24,
    ) -> list[BookingEntity]:
        """
        Get bookings pending confirmation that may need to be expired.

        Args:
            older_than_hours: Only return bookings older than this

        Returns:
            List of pending bookings
        """
        ...

    def get_sessions_to_start(
        self,
        *,
        buffer_minutes: int = 5,
    ) -> list[BookingEntity]:
        """
        Get confirmed bookings ready to start.

        Args:
            buffer_minutes: Time window around start time

        Returns:
            List of bookings ready to start
        """
        ...

    def get_sessions_to_end(
        self,
        *,
        grace_period_minutes: int = 15,
    ) -> list[BookingEntity]:
        """
        Get in-progress sessions past their end time.

        Args:
            grace_period_minutes: Grace period after end time

        Returns:
            List of sessions to end
        """
        ...

    def get_upcoming_for_reminder(
        self,
        *,
        hours_until: int,
        window_minutes: int = 30,
    ) -> list[BookingEntity]:
        """
        Get confirmed bookings for sending reminders.

        Args:
            hours_until: Hours before session
            window_minutes: Time window for matching

        Returns:
            List of bookings needing reminders
        """
        ...

    def count_by_student(
        self,
        student_id: int,
        *,
        states: list[SessionState] | None = None,
    ) -> int:
        """
        Count bookings for a student.

        Args:
            student_id: Student's user ID
            states: Filter by session states

        Returns:
            Count of matching bookings
        """
        ...

    def count_by_tutor(
        self,
        tutor_id: int,
        *,
        states: list[SessionState] | None = None,
    ) -> int:
        """
        Count bookings for a tutor.

        Args:
            tutor_id: Tutor's user ID
            states: Filter by session states

        Returns:
            Count of matching bookings
        """
        ...

    def check_time_conflict(
        self,
        tutor_id: int,
        start_time: datetime,
        end_time: datetime,
        *,
        exclude_booking_id: int | None = None,
    ) -> bool:
        """
        Check if a time slot conflicts with existing bookings.

        Args:
            tutor_id: Tutor's user ID
            start_time: Proposed start time
            end_time: Proposed end time
            exclude_booking_id: Booking to exclude from check

        Returns:
            True if conflict exists, False otherwise
        """
        ...
