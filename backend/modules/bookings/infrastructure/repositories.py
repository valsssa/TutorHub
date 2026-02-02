"""SQLAlchemy repository implementation for bookings."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.bookings import Booking
from modules.bookings.domain.entities import BookingEntity
from modules.bookings.domain.repositories import BookingRepository
from modules.bookings.domain.status import (
    ACTIVE_SESSION_STATES,
    DisputeState,
    PaymentState,
    SessionOutcome,
    SessionState,
)


class OptimisticLockError(Exception):
    """Raised when optimistic locking detects a version mismatch."""

    def __init__(self, expected_version: int, actual_version: int):
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Booking has been modified by another request. "
            f"Expected version {expected_version}, but current version is {actual_version}."
        )


@dataclass(slots=True)
class BookingRepositoryImpl(BookingRepository):
    """Repository backed by SQLAlchemy ORM."""

    db: Session

    def get_by_id(self, booking_id: int) -> BookingEntity | None:
        """
        Get a booking by its ID.

        Args:
            booking_id: Booking's unique identifier

        Returns:
            BookingEntity if found, None otherwise
        """
        booking = (
            self.db.query(Booking)
            .filter(Booking.id == booking_id, Booking.deleted_at.is_(None))
            .first()
        )
        if not booking:
            return None
        return self._to_entity(booking)

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
        query = self._base_query().filter(Booking.student_id == student_id)

        if states:
            state_values = [s.value for s in states]
            query = query.filter(Booking.session_state.in_(state_values))

        if from_date:
            query = query.filter(Booking.start_time >= from_date)

        if to_date:
            query = query.filter(Booking.start_time <= to_date)

        query = query.order_by(Booking.start_time.desc())

        offset = (page - 1) * page_size
        bookings = query.offset(offset).limit(page_size).all()

        return [self._to_entity(b) for b in bookings]

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
        from models import TutorProfile

        tutor_profile = (
            self.db.query(TutorProfile)
            .filter(TutorProfile.user_id == tutor_id, TutorProfile.deleted_at.is_(None))
            .first()
        )
        if not tutor_profile:
            return []

        query = self._base_query().filter(Booking.tutor_profile_id == tutor_profile.id)

        if states:
            state_values = [s.value for s in states]
            query = query.filter(Booking.session_state.in_(state_values))

        if from_date:
            query = query.filter(Booking.start_time >= from_date)

        if to_date:
            query = query.filter(Booking.start_time <= to_date)

        query = query.order_by(Booking.start_time.desc())

        offset = (page - 1) * page_size
        bookings = query.offset(offset).limit(page_size).all()

        return [self._to_entity(b) for b in bookings]

    def create(self, booking: BookingEntity) -> BookingEntity:
        """
        Create a new booking.

        Args:
            booking: Booking entity to create

        Returns:
            Created booking with populated ID
        """
        now = datetime.now(UTC)
        model = self._to_model(booking)
        model.created_at = now
        model.updated_at = now
        model.version = 1

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

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
        if booking.id is None:
            raise ValueError("Cannot update booking without ID")

        model = (
            self.db.query(Booking)
            .filter(Booking.id == booking.id, Booking.deleted_at.is_(None))
            .first()
        )
        if not model:
            raise ValueError(f"Booking with ID {booking.id} not found")

        if model.version != booking.version:
            raise OptimisticLockError(
                expected_version=booking.version,
                actual_version=model.version,
            )

        now = datetime.now(UTC)
        model.student_id = booking.student_id
        model.tutor_profile_id = booking.tutor_profile_id
        model.start_time = booking.start_time
        model.end_time = booking.end_time
        model.student_tz = booking.timezone

        model.session_state = booking.session_state.value
        model.session_outcome = booking.session_outcome.value if booking.session_outcome else None
        model.payment_state = booking.payment_state.value
        model.dispute_state = booking.dispute_state.value

        model.rate_cents = booking.amount_cents
        model.currency = booking.currency
        model.platform_fee_cents = booking.platform_fee_cents

        model.subject_id = booking.subject_id
        model.subject_name = booking.subject_name
        model.package_id = booking.package_id
        model.pricing_option_id = booking.pricing_option_id

        model.meeting_url = booking.meeting_url
        model.zoom_meeting_id = booking.meeting_id
        model.video_provider = booking.meeting_provider

        model.stripe_checkout_session_id = booking.stripe_session_id
        # payment_intent_id stored elsewhere or managed differently

        model.notes_student = booking.student_notes
        model.notes_tutor = booking.tutor_notes
        model.cancellation_reason = booking.cancellation_reason

        model.confirmed_at = booking.confirmed_at
        model.cancelled_at = booking.cancelled_at
        # completed_at stored in entity but model may not have direct column

        model.updated_at = now
        model.version = booking.version + 1

        self.db.commit()
        self.db.refresh(model)

        return self._to_entity(model)

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
        cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)

        bookings = (
            self._base_query()
            .filter(
                Booking.session_state == SessionState.REQUESTED.value,
                Booking.created_at <= cutoff,
            )
            .all()
        )

        return [self._to_entity(b) for b in bookings]

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
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=buffer_minutes)
        window_end = now + timedelta(minutes=buffer_minutes)

        bookings = (
            self._base_query()
            .filter(
                Booking.session_state == SessionState.SCHEDULED.value,
                Booking.start_time >= window_start,
                Booking.start_time <= window_end,
            )
            .all()
        )

        return [self._to_entity(b) for b in bookings]

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
        cutoff = datetime.now(UTC) - timedelta(minutes=grace_period_minutes)

        bookings = (
            self._base_query()
            .filter(
                Booking.session_state == SessionState.ACTIVE.value,
                Booking.end_time <= cutoff,
            )
            .all()
        )

        return [self._to_entity(b) for b in bookings]

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
        now = datetime.now(UTC)
        target_time = now + timedelta(hours=hours_until)
        window_start = target_time - timedelta(minutes=window_minutes // 2)
        window_end = target_time + timedelta(minutes=window_minutes // 2)

        bookings = (
            self._base_query()
            .filter(
                Booking.session_state == SessionState.SCHEDULED.value,
                Booking.start_time >= window_start,
                Booking.start_time <= window_end,
            )
            .all()
        )

        return [self._to_entity(b) for b in bookings]

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
        query = self._base_query().filter(Booking.student_id == student_id)

        if states:
            state_values = [s.value for s in states]
            query = query.filter(Booking.session_state.in_(state_values))

        return query.count()

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
        from models import TutorProfile

        tutor_profile = (
            self.db.query(TutorProfile)
            .filter(TutorProfile.user_id == tutor_id, TutorProfile.deleted_at.is_(None))
            .first()
        )
        if not tutor_profile:
            return 0

        query = self._base_query().filter(Booking.tutor_profile_id == tutor_profile.id)

        if states:
            state_values = [s.value for s in states]
            query = query.filter(Booking.session_state.in_(state_values))

        return query.count()

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
        from models import TutorProfile

        tutor_profile = (
            self.db.query(TutorProfile)
            .filter(TutorProfile.user_id == tutor_id, TutorProfile.deleted_at.is_(None))
            .first()
        )
        if not tutor_profile:
            return False

        active_states = [s.value for s in ACTIVE_SESSION_STATES]

        query = (
            self._base_query()
            .filter(
                Booking.tutor_profile_id == tutor_profile.id,
                Booking.session_state.in_(active_states),
                or_(
                    and_(
                        Booking.start_time < end_time,
                        Booking.end_time > start_time,
                    ),
                ),
            )
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        return query.count() > 0

    def _base_query(self):
        """Base query filtering out soft-deleted bookings."""
        return self.db.query(Booking).filter(Booking.deleted_at.is_(None))

    def _to_entity(self, model: Booking) -> BookingEntity:
        """
        Convert SQLAlchemy model to domain entity.

        Args:
            model: Booking SQLAlchemy model

        Returns:
            BookingEntity domain object
        """
        session_state = SessionState(model.session_state)
        session_outcome = SessionOutcome(model.session_outcome) if model.session_outcome else None
        payment_state = PaymentState(model.payment_state)
        dispute_state = DisputeState(model.dispute_state)

        tutor_id = None
        if model.tutor_profile:
            tutor_id = model.tutor_profile.user_id

        amount_cents = model.rate_cents or 0
        if not amount_cents and model.total_amount:
            amount_cents = int(model.total_amount * 100)

        return BookingEntity(
            id=model.id,
            student_id=model.student_id,
            tutor_id=tutor_id or 0,
            tutor_profile_id=model.tutor_profile_id,
            start_time=model.start_time,
            end_time=model.end_time,
            timezone=model.student_tz or "UTC",
            session_state=session_state,
            session_outcome=session_outcome,
            payment_state=payment_state,
            dispute_state=dispute_state,
            amount_cents=amount_cents,
            currency=model.currency or "USD",
            platform_fee_cents=model.platform_fee_cents or 0,
            subject_id=model.subject_id,
            subject_name=model.subject_name,
            package_id=model.package_id,
            pricing_option_id=model.pricing_option_id,
            meeting_url=model.meeting_url or model.join_url,
            meeting_id=model.zoom_meeting_id,
            meeting_provider=model.video_provider,
            stripe_session_id=model.stripe_checkout_session_id,
            payment_intent_id=None,
            student_notes=model.notes_student,
            tutor_notes=model.notes_tutor,
            cancellation_reason=model.cancellation_reason,
            created_at=model.created_at,
            updated_at=model.updated_at,
            confirmed_at=model.confirmed_at,
            cancelled_at=model.cancelled_at,
            completed_at=None,
            version=model.version or 1,
        )

    def _to_model(self, entity: BookingEntity) -> Booking:
        """
        Convert domain entity to SQLAlchemy model for creation.

        Args:
            entity: BookingEntity domain object

        Returns:
            Booking SQLAlchemy model (for insertion)
        """
        hourly_rate = Decimal(entity.amount_cents) / 100 if entity.amount_cents else Decimal("0.00")
        total_amount = hourly_rate

        model = Booking(
            student_id=entity.student_id,
            tutor_profile_id=entity.tutor_profile_id,
            start_time=entity.start_time,
            end_time=entity.end_time,
            student_tz=entity.timezone,
            session_state=entity.session_state.value,
            session_outcome=entity.session_outcome.value if entity.session_outcome else None,
            payment_state=entity.payment_state.value,
            dispute_state=entity.dispute_state.value,
            rate_cents=entity.amount_cents,
            currency=entity.currency,
            platform_fee_cents=entity.platform_fee_cents,
            hourly_rate=hourly_rate,
            total_amount=total_amount,
            subject_id=entity.subject_id,
            subject_name=entity.subject_name,
            package_id=entity.package_id,
            pricing_option_id=entity.pricing_option_id,
            meeting_url=entity.meeting_url,
            zoom_meeting_id=entity.meeting_id,
            video_provider=entity.meeting_provider,
            stripe_checkout_session_id=entity.stripe_session_id,
            notes_student=entity.student_notes,
            notes_tutor=entity.tutor_notes,
            cancellation_reason=entity.cancellation_reason,
            confirmed_at=entity.confirmed_at,
            cancelled_at=entity.cancelled_at,
            version=entity.version,
        )

        if entity.id is not None:
            model.id = entity.id

        return model
