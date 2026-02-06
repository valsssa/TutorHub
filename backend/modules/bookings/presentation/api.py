"""
Clean booking API endpoints following presentation layer pattern.
Consolidates all booking routes with shared error handling and authorization.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from core.datetime_utils import utc_now
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from core.dependencies import StudentUser, get_current_tutor_profile, get_current_user
from core.query_helpers import get_or_404
from core.transactions import atomic_operation
from database import get_db
from models import Booking, TutorProfile, User
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import DisputeState, SessionState
from modules.bookings.policy_engine import ReschedulePolicy
from modules.bookings.schemas import (
    BookingCancelRequest,
    BookingConfirmRequest,
    BookingCreateRequest,
    BookingDeclineRequest,
    BookingDTO,
    BookingListResponse,
    BookingRescheduleRequest,
    BookingStatsResponse,
    DisputeCreateRequest,
    DisputeResolveRequest,
    MarkNoShowRequest,
    RecordJoinRequest,
)
from modules.bookings.service import BookingService, booking_to_dto

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["bookings"])


def _add_booking_cache_headers(response: Response, booking: Booking) -> None:
    """
    Add cache invalidation headers to booking responses.

    These headers help the frontend handle race conditions between WebSocket
    broadcasts and API responses by providing version and timestamp information.

    Headers added:
    - X-Booking-Version: The optimistic locking version of the booking
    - X-Booking-Updated-At: ISO timestamp of last modification
    - Cache-Control: no-store to prevent caching of booking state

    Frontend should compare X-Booking-Version with cached data and only apply
    updates if the version is >= the cached version.
    """
    response.headers["X-Booking-Version"] = str(booking.version or 1)
    response.headers["X-Booking-Updated-At"] = (
        booking.updated_at.isoformat() if booking.updated_at else datetime.now(UTC).isoformat()
    )
    # Prevent intermediate caching of booking state
    response.headers["Cache-Control"] = "no-store"


async def _broadcast_availability_update(tutor_profile_id: int, tutor_user_id: int) -> None:
    """Broadcast availability change to all connected clients."""
    try:
        from modules.messages.websocket import manager

        message = {
            "type": "availability_updated",
            "tutor_profile_id": tutor_profile_id,
            "tutor_user_id": tutor_user_id,
        }
        await manager.broadcast_to_all(message)
    except Exception as e:
        logger.warning("Failed to broadcast availability update: %s", e)


# ============================================================================
# Shared Authorization Helpers
# ============================================================================


def _verify_booking_ownership(booking: Booking, current_user: User, db: Session) -> None:
    """Verify user has access to booking (student or tutor)."""
    if current_user.role == "student":
        if booking.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this booking",
            )
    elif current_user.role == "tutor":
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
        if not tutor_profile or booking.tutor_profile_id != tutor_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this booking",
            )


def _get_booking_or_404(
    booking_id: int,
    db: Session,
    *,
    current_user: User | None = None,
    verify_ownership: bool = True,
) -> Booking:
    """Get booking by ID with optional ownership check."""
    booking = (
        db.query(Booking)
        .options(
            joinedload(Booking.tutor_profile).joinedload(TutorProfile.user).joinedload(User.profile),
            joinedload(Booking.student).joinedload(User.profile),
            joinedload(Booking.subject),
        )
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    if verify_ownership and current_user:
        _verify_booking_ownership(booking, current_user, db)

    return booking


# NOTE: The _require_role helper has been removed in favor of using
# StudentUser/TutorUser/AdminUser type aliases from core.dependencies
# which automatically enforce role requirements via FastAPI dependency injection.


# ============================================================================
# Stats Endpoint (must be before /bookings/{booking_id} to avoid path conflict)
# ============================================================================


@router.get("/bookings/stats", response_model=BookingStatsResponse)
async def get_booking_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get booking statistics for the current user.

    Returns counts by status, total hours, and next upcoming booking.
    Students see their student bookings, tutors see their tutor bookings.
    """
    from sqlalchemy import func

    # Build base query filtered by user role
    if current_user.role == "student":
        base_filter = Booking.student_id == current_user.id
    elif current_user.role == "tutor":
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
        if not tutor_profile:
            return BookingStatsResponse(
                total_bookings=0,
                upcoming_count=0,
                pending_count=0,
                completed_count=0,
                cancelled_count=0,
                active_count=0,
                total_hours=0.0,
                next_booking=None,
            )
        base_filter = Booking.tutor_profile_id == tutor_profile.id
    else:
        # Admin/owner can see all (or restrict as needed)
        base_filter = True

    now = datetime.now(UTC)

    # Count by status
    total = db.query(func.count(Booking.id)).filter(base_filter).scalar() or 0

    upcoming = (
        db.query(func.count(Booking.id))
        .filter(
            base_filter,
            Booking.session_state == SessionState.SCHEDULED.value,
            Booking.start_time >= now,
        )
        .scalar()
        or 0
    )

    pending = (
        db.query(func.count(Booking.id))
        .filter(base_filter, Booking.session_state == SessionState.REQUESTED.value)
        .scalar()
        or 0
    )

    completed = (
        db.query(func.count(Booking.id))
        .filter(
            base_filter,
            Booking.session_state == SessionState.ENDED.value,
            Booking.session_outcome == "COMPLETED",
        )
        .scalar()
        or 0
    )

    cancelled = (
        db.query(func.count(Booking.id))
        .filter(
            base_filter,
            Booking.session_state.in_([SessionState.CANCELLED.value, SessionState.EXPIRED.value]),
        )
        .scalar()
        or 0
    )

    active = (
        db.query(func.count(Booking.id))
        .filter(base_filter, Booking.session_state == SessionState.ACTIVE.value)
        .scalar()
        or 0
    )

    # Calculate total hours from completed sessions
    completed_bookings = (
        db.query(Booking.start_time, Booking.end_time)
        .filter(
            base_filter,
            Booking.session_state == SessionState.ENDED.value,
            Booking.session_outcome == "COMPLETED",
        )
        .all()
    )
    total_hours = sum(
        (b.end_time - b.start_time).total_seconds() / 3600
        for b in completed_bookings
        if b.start_time and b.end_time
    )

    # Get next upcoming booking
    next_booking = (
        db.query(Booking.start_time)
        .filter(
            base_filter,
            Booking.session_state.in_([SessionState.SCHEDULED.value, SessionState.REQUESTED.value]),
            Booking.start_time >= now,
        )
        .order_by(Booking.start_time.asc())
        .first()
    )

    return BookingStatsResponse(
        total_bookings=total,
        upcoming_count=upcoming,
        pending_count=pending,
        completed_count=completed,
        cancelled_count=cancelled,
        active_count=active,
        total_hours=round(total_hours, 1),
        next_booking=next_booking[0] if next_booking else None,
    )


# ============================================================================
# Student Booking Endpoints
# ============================================================================


@router.post(
    "/bookings",
    response_model=BookingDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create new booking (student only)",
)
async def create_booking(
    request: BookingCreateRequest,
    response: Response,
    current_user: StudentUser,
    db: Session = Depends(get_db),
):
    """
    Create tutoring session booking with automatic conflict checking and pricing.

    - Validates tutor availability and checks for conflicts
    - Checks external calendar (Google Calendar) for conflicts if tutor has it connected
    - Calculates pricing with platform fee
    - Auto-confirms if tutor has auto_confirm enabled
    - Deducts package credit if package_id provided
    """

    try:
        from core.soft_delete import filter_active
        from modules.bookings.services.response_tracking import ResponseTrackingService

        service = BookingService(db)

        # Pre-flight check: Get tutor profile and user for external calendar check
        # This catches events added to Google Calendar since last sync
        tutor_profile = (
            filter_active(db.query(TutorProfile), TutorProfile)
            .filter(TutorProfile.id == request.tutor_profile_id)
            .first()
        )
        if tutor_profile and tutor_profile.user:
            end_at = request.start_at + timedelta(minutes=request.duration_minutes)
            await service.check_external_calendar_conflict(
                tutor_user=tutor_profile.user,
                start_at=request.start_at,
                end_at=end_at,
            )

        booking = service.create_booking(
            student_id=current_user.id,
            tutor_profile_id=request.tutor_profile_id,
            start_at=request.start_at,
            duration_minutes=request.duration_minutes,
            lesson_type=request.lesson_type,
            subject_id=request.subject_id,
            notes_student=request.notes_student,
            package_id=request.use_package_id,
        )

        # Log booking creation for response time tracking
        response_tracker = ResponseTrackingService(db)
        response_tracker.log_booking_created(booking)

        # If auto-confirmed (SCHEDULED state), log the auto_confirmed action
        if booking.session_state == SessionState.SCHEDULED.value:
            response_tracker.log_tutor_response(booking, "auto_confirmed")

        db.commit()
        db.refresh(booking)

        await _broadcast_availability_update(
            tutor_profile_id=booking.tutor_profile_id,
            tutor_user_id=booking.tutor_profile.user_id if booking.tutor_profile else 0,
        )

        _add_booking_cache_headers(response, booking)
        return booking_to_dto(booking, db)

    except HTTPException as e:
        # Handle 409 Conflict errors - preserve external calendar conflict details
        if e.status_code == status.HTTP_409_CONFLICT:
            # If the error already has structured detail (e.g., external_calendar_conflict),
            # preserve it rather than wrapping it
            if isinstance(e.detail, dict) and e.detail.get("error") == "external_calendar_conflict":
                raise  # Re-raise the external calendar conflict as-is
            # Otherwise, enhance with standard slot unavailable message
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "slot_no_longer_available",
                    "message": "This time slot is no longer available. Please refresh and select a different time.",
                    "suggested_action": "refresh_slots",
                    "original_error": str(e.detail) if isinstance(e.detail, str) else e.detail,
                },
            )
        raise
    except IntegrityError as e:
        # Handle database-level constraint violation (exclusion constraint for overlapping bookings)
        # This is a safety net in case the application-level locking somehow fails
        db.rollback()
        error_str = str(e).lower()
        if "bookings_no_time_overlap" in error_str or "overlap" in error_str:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "slot_no_longer_available",
                    "message": "This time slot is no longer available. Please refresh and select a different time.",
                    "suggested_action": "refresh_slots",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "booking_conflict",
                "message": "Booking conflicts with existing data. Please refresh and try again.",
                "suggested_action": "refresh_slots",
            },
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create booking: {str(e)}",
        )


@router.get("/bookings", response_model=BookingListResponse)
async def list_bookings(
    status_filter: str | None = Query(None, alias="status"),
    role: str | None = Query("student", pattern="^(student|tutor)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List bookings for current user with filtering and pagination.

    - Students see their bookings as student
    - Tutors see their bookings as tutor
    - Filter by status: upcoming, pending, completed, cancelled
    """
    query = db.query(Booking).options(
        joinedload(Booking.tutor_profile).joinedload(TutorProfile.user).joinedload(User.profile),
        joinedload(Booking.student).joinedload(User.profile),
        joinedload(Booking.subject),
    )

    # Filter by user role
    if current_user.role == "student" or role == "student":
        query = query.filter(Booking.student_id == current_user.id)
    elif current_user.role == "tutor" or role == "tutor":
        tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
        if not tutor_profile:
            return BookingListResponse(bookings=[], total=0, page=page, page_size=page_size)
        query = query.filter(Booking.tutor_profile_id == tutor_profile.id)

    # Apply status filter using new session_state field
    if status_filter:
        if status_filter.lower() == "upcoming":
            query = query.filter(
                Booking.session_state.in_([
                    SessionState.REQUESTED.value,
                    SessionState.SCHEDULED.value,
                    SessionState.ACTIVE.value,
                ]),
                Booking.start_time >= utc_now(),
            )
        elif status_filter.lower() == "pending":
            query = query.filter(Booking.session_state == SessionState.REQUESTED.value)
        elif status_filter.lower() == "completed":
            query = query.filter(
                Booking.session_state == SessionState.ENDED.value,
                Booking.session_outcome == "COMPLETED",
            )
        elif status_filter.lower() == "cancelled":
            query = query.filter(
                Booking.session_state.in_([
                    SessionState.CANCELLED.value,
                    SessionState.EXPIRED.value,
                ])
            )
        elif status_filter.lower() == "active":
            query = query.filter(Booking.session_state == SessionState.ACTIVE.value)
        elif status_filter.lower() == "scheduled":
            query = query.filter(Booking.session_state == SessionState.SCHEDULED.value)

    # Pagination
    total = query.count()
    bookings = query.order_by(Booking.start_time.desc()).offset((page - 1) * page_size).limit(page_size).all()

    booking_dtos = [booking_to_dto(booking, db) for booking in bookings]

    return BookingListResponse(
        bookings=booking_dtos,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/bookings/{booking_id}", response_model=BookingDTO)
async def get_booking(
    booking_id: int,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed booking information with authorization check."""
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)
    _add_booking_cache_headers(response, booking)
    return booking_to_dto(booking, db)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingDTO)
async def cancel_booking(
    booking_id: int,
    request: BookingCancelRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel booking with refund policy enforcement.

    - Students and tutors can cancel their bookings
    - Refund policy: >= 12h before = full refund, < 12h = no refund
    - Restores package credit if applicable

    Race Condition Prevention:
    - Uses row-level locking (SELECT FOR UPDATE) to prevent race conditions
      with the start_sessions background job
    - Re-checks cancellability after acquiring the lock to ensure the booking
      state hasn't changed between the initial check and the lock acquisition

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    - State machine updates are atomic with package credit restoration
    """
    # First, verify the booking exists and user has access (without lock)
    _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)

    try:
        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            # Acquire row-level lock to prevent race conditions with start_sessions job
            # This ensures the booking state doesn't change while we're processing the cancel
            locked_booking = BookingStateMachine.get_booking_with_lock(db, booking_id, nowait=False)

            if not locked_booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            # Re-check cancellability after acquiring lock
            # The booking state may have changed between the initial check and lock acquisition
            # (e.g., start_sessions job may have transitioned SCHEDULED -> ACTIVE)
            if not BookingStateMachine.is_cancellable(locked_booking.session_state):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Booking cannot be cancelled (current state: {locked_booking.session_state}). "
                    "The session may have already started.",
                )

            service = BookingService(db)
            cancelled_booking = service.cancel_booking(
                booking=locked_booking,
                cancelled_by_role=current_user.role.upper(),
                reason=request.reason,
            )

            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(cancelled_booking)

        await _broadcast_availability_update(
            tutor_profile_id=cancelled_booking.tutor_profile_id,
            tutor_user_id=cancelled_booking.tutor_profile.user_id if cancelled_booking.tutor_profile else 0,
        )

        _add_booking_cache_headers(response, cancelled_booking)
        return booking_to_dto(cancelled_booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel booking: {str(e)}",
        )


@router.post("/bookings/{booking_id}/reschedule", response_model=BookingDTO)
async def reschedule_booking(
    booking_id: int,
    request: BookingRescheduleRequest,
    response: Response,
    current_user: StudentUser,
    db: Session = Depends(get_db),
):
    """
    Reschedule booking to new time (student only).

    - Must be >= 12h before original time
    - Checks new time for tutor availability conflicts
    """
    booking = get_or_404(
        db, Booking,
        {"id": booking_id, "student_id": current_user.id},
        detail="Booking not found"
    )

    try:
        service = BookingService(db)

        # Validate reschedule timing
        decision = ReschedulePolicy.evaluate_reschedule(
            booking_start_at=booking.start_time,
            now=utc_now(),
            new_start_at=request.new_start_at,
        )

        if not decision.allow:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=decision.message,
            )

        # Calculate new end time
        duration = (booking.end_time - booking.start_time).total_seconds() / 60
        new_end_at = request.new_start_at + timedelta(minutes=duration)

        # Check conflicts at new time (internal bookings and availability)
        if booking.tutor_profile:
            conflicts = service.check_conflicts(
                tutor_profile_id=booking.tutor_profile.id,
                start_at=request.new_start_at,
                end_at=new_end_at,
                exclude_booking_id=booking.id,
            )
            if conflicts:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "slot_no_longer_available",
                        "message": "This time slot is no longer available. Please refresh and select a different time.",
                        "suggested_action": "refresh_slots",
                        "conflict_reason": conflicts,
                    },
                )

            # Check external calendar for conflicts at new time
            if booking.tutor_profile.user:
                await service.check_external_calendar_conflict(
                    tutor_user=booking.tutor_profile.user,
                    start_at=request.new_start_at,
                    end_at=new_end_at,
                )

        # Update booking
        booking.start_time = request.new_start_at
        booking.end_time = new_end_at
        booking.notes = (booking.notes or "") + f"\n[Rescheduled at {utc_now()}]"

        db.commit()
        db.refresh(booking)

        await _broadcast_availability_update(
            tutor_profile_id=booking.tutor_profile_id,
            tutor_user_id=booking.tutor_profile.user_id if booking.tutor_profile else 0,
        )

        _add_booking_cache_headers(response, booking)
        return booking_to_dto(booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule booking: {str(e)}",
        )


# ============================================================================
# Tutor Booking Endpoints
# ============================================================================


@router.post("/tutor/bookings/{booking_id}/confirm", response_model=BookingDTO)
async def confirm_booking(
    booking_id: int,
    request: BookingConfirmRequest,
    response: Response,
    tutor_profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Confirm pending booking (tutor only).

    - Changes status from PENDING to CONFIRMED
    - Creates Zoom meeting and generates join URL
    - Uses row-level locking to prevent race conditions
    - If Zoom fails, booking is still confirmed but flagged for retry

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    - State machine updates (session_state, payment_state, confirmed_at) are atomic
    """
    try:
        from modules.bookings.services.response_tracking import ResponseTrackingService
        from modules.integrations.video_meeting_service import create_meeting_for_booking

        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            # Acquire row-level lock to prevent race conditions
            # (e.g., concurrent expiry job or duplicate confirm requests)
            booking = BookingStateMachine.get_booking_with_lock(db, booking_id)

            if not booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            if booking.tutor_profile_id != tutor_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            # Use state machine to validate and transition (idempotent)
            # State machine does NOT commit - all changes are atomic within this block
            result = BookingStateMachine.accept_booking(booking)

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message or f"Cannot confirm booking with state {booking.session_state}",
                )

            # Only update additional fields if this wasn't an idempotent no-op
            if not result.already_in_target_state:
                # Create video meeting using tutor's preferred provider
                meeting_result = await create_meeting_for_booking(db, booking, tutor_profile)

                if meeting_result.success:
                    booking.join_url = meeting_result.join_url
                    booking.meeting_url = meeting_result.host_url
                    booking.video_provider = meeting_result.provider

                    # Provider-specific fields
                    if meeting_result.provider == "zoom" and meeting_result.meeting_id:
                        booking.zoom_meeting_id = meeting_result.meeting_id
                        booking.zoom_meeting_pending = False
                    elif meeting_result.provider == "google_meet" and meeting_result.join_url:
                        booking.google_meet_link = meeting_result.join_url

                    logger.info(
                        "Created %s meeting for booking %d",
                        meeting_result.provider,
                        booking.id,
                    )
                else:
                    # Meeting creation failed - flag for retry if applicable
                    logger.error(
                        "Failed to create meeting for booking %d using %s: %s",
                        booking.id,
                        meeting_result.provider,
                        meeting_result.error_message,
                    )
                    if meeting_result.needs_retry:
                        booking.zoom_meeting_pending = True
                    booking.video_provider = meeting_result.provider

                    # Generate fallback URL if no join_url
                    if not booking.join_url:
                        service = BookingService(db)
                        booking.join_url = service._generate_join_url(booking.id)

                # Add tutor notes
                if request.notes_tutor:
                    booking.notes_tutor = request.notes_tutor

                # Track response time
                response_tracker = ResponseTrackingService(db)
                response_tracker.log_tutor_response(booking, "confirmed")

            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(booking)

        await _broadcast_availability_update(
            tutor_profile_id=booking.tutor_profile_id,
            tutor_user_id=tutor_profile.user_id,
        )

        _add_booking_cache_headers(response, booking)
        return booking_to_dto(booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm booking: {str(e)}",
        )


@router.post("/tutor/bookings/{booking_id}/decline", response_model=BookingDTO)
async def decline_booking(
    booking_id: int,
    request: BookingDeclineRequest,
    response: Response,
    tutor_profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Decline pending booking (tutor only).

    - Changes status to CANCELLED_BY_TUTOR
    - Automatically refunds student
    - Uses row-level locking to prevent race conditions

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    - State machine updates are atomic with response tracking
    """
    try:
        from modules.bookings.services.response_tracking import ResponseTrackingService

        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            # Acquire row-level lock to prevent race conditions
            booking = BookingStateMachine.get_booking_with_lock(db, booking_id)

            if not booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            if booking.tutor_profile_id != tutor_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            service = BookingService(db)
            declined_booking = service.cancel_booking(
                booking=booking,
                cancelled_by_role="TUTOR",
                reason=request.reason,
            )

            # Track response time
            response_tracker = ResponseTrackingService(db)
            response_tracker.log_tutor_response(booking, "cancelled")

            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(declined_booking)

        await _broadcast_availability_update(
            tutor_profile_id=declined_booking.tutor_profile_id,
            tutor_user_id=tutor_profile.user_id,
        )

        _add_booking_cache_headers(response, declined_booking)
        return booking_to_dto(declined_booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decline booking: {str(e)}",
        )


@router.post("/tutor/bookings/{booking_id}/mark-no-show-student", response_model=BookingDTO)
async def mark_student_no_show(
    booking_id: int,
    request: MarkNoShowRequest,
    response: Response,
    tutor_profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Mark student as no-show (tutor only).

    - Must be 10+ minutes after start time and within 24h
    - Tutor earns full payment
    - Uses row-level locking to prevent race conditions with concurrent reports
    - If both parties report no-show, auto-escalates to dispute for admin review

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    - State machine updates are atomic with dispute escalation if needed
    """
    # First verify the booking exists and belongs to this tutor (without lock)
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.tutor_profile_id == tutor_profile.id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    try:
        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            service = BookingService(db)
            # Use row-level locking to prevent race conditions
            no_show_booking, escalated = service.mark_no_show(
                booking=booking,
                reporter_role="TUTOR",
                notes=request.notes,
                use_lock=True,  # Acquire row lock for race condition safety
            )

            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(no_show_booking)

        _add_booking_cache_headers(response, no_show_booking)
        result = booking_to_dto(no_show_booking, db)

        # Log if escalated to dispute due to conflicting reports
        if escalated:
            logger.warning(
                "Conflicting no-show reports for booking %d - auto-escalated to dispute",
                booking_id,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark no-show: {str(e)}",
        )


@router.post("/tutor/bookings/{booking_id}/mark-no-show-tutor", response_model=BookingDTO)
async def mark_tutor_no_show(
    booking_id: int,
    request: MarkNoShowRequest,
    response: Response,
    current_user: StudentUser,
    db: Session = Depends(get_db),
):
    """
    Mark tutor as no-show (student only).

    - Must be 10+ minutes after start time and within 24h
    - Student receives full refund
    - Uses row-level locking to prevent race conditions with concurrent reports
    - If both parties report no-show, auto-escalates to dispute for admin review

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    - State machine updates are atomic with package credit restoration if needed
    """
    # First verify the booking exists and belongs to this student (without lock)
    booking = get_or_404(
        db, Booking,
        {"id": booking_id, "student_id": current_user.id},
        detail="Booking not found"
    )

    try:
        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            service = BookingService(db)
            # Use row-level locking to prevent race conditions
            no_show_booking, escalated = service.mark_no_show(
                booking=booking,
                reporter_role="STUDENT",
                notes=request.notes,
                use_lock=True,  # Acquire row lock for race condition safety
            )

            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(no_show_booking)

        _add_booking_cache_headers(response, no_show_booking)
        result = booking_to_dto(no_show_booking, db)

        # Log if escalated to dispute due to conflicting reports
        if escalated:
            logger.warning(
                "Conflicting no-show reports for booking %d - auto-escalated to dispute",
                booking_id,
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark tutor no-show: {str(e)}",
        )


# ============================================================================
# Dispute Endpoints
# ============================================================================


@router.post("/bookings/{booking_id}/dispute", response_model=BookingDTO)
async def open_dispute(
    booking_id: int,
    request: DisputeCreateRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Open a dispute on a booking (student or tutor).

    - Can only dispute bookings in terminal states (ENDED, CANCELLED, EXPIRED)
    - Cannot dispute if already has an open dispute

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    """
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)

    try:
        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            result = BookingStateMachine.open_dispute(
                booking=booking,
                reason=request.reason,
                disputed_by_user_id=current_user.id,
            )

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message or "Cannot open dispute",
                )

            booking.updated_at = datetime.now(UTC)
            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(booking)

        _add_booking_cache_headers(response, booking)
        return booking_to_dto(booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to open dispute: {str(e)}",
        )


@router.post("/admin/bookings/{booking_id}/resolve", response_model=BookingDTO)
async def resolve_dispute(
    booking_id: int,
    request: DisputeResolveRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resolve a dispute (admin only).

    - Resolves to RESOLVED_UPHELD (original decision stands) or RESOLVED_REFUNDED (refund granted)
    - Can issue full or partial refund

    Transaction Safety:
    - Uses atomic_operation to ensure all state changes commit together or rollback
    - Dispute resolution is atomic with package credit restoration if needed
    """
    # Require admin role
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can resolve disputes",
        )

    booking = _get_booking_or_404(booking_id, db, current_user=None, verify_ownership=False)

    try:
        # Use atomic_operation to ensure all state changes commit together
        with atomic_operation(db):
            resolution = DisputeState(request.resolution)
            result = BookingStateMachine.resolve_dispute(
                booking=booking,
                resolution=resolution,
                resolved_by_user_id=current_user.id,
                notes=request.notes,
                refund_amount_cents=request.refund_amount_cents,
            )

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error_message or "Cannot resolve dispute",
                )

            # Restore package credit if dispute resolution includes refund
            if result.restore_package_credit and booking.package_id:
                service = BookingService(db)
                service._restore_package_credit(booking.package_id)

            booking.updated_at = datetime.now(UTC)
            # atomic_operation commits all changes together on context exit

        # Refresh after commit to get updated state
        db.refresh(booking)

        _add_booking_cache_headers(response, booking)
        return booking_to_dto(booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve dispute: {str(e)}",
        )


# ============================================================================
# Meeting Management Endpoints
# ============================================================================


@router.post("/bookings/{booking_id}/regenerate-meeting", response_model=BookingDTO)
async def regenerate_meeting(
    booking_id: int,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate Zoom meeting link for a booking.

    - Can be used when initial Zoom meeting creation failed
    - Only works for bookings in SCHEDULED or ACTIVE state
    - Both tutors and students can regenerate the meeting link
    """
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)

    # Validate booking state
    if booking.session_state not in [SessionState.SCHEDULED.value, SessionState.ACTIVE.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot regenerate meeting for booking with state {booking.session_state}. "
            "Meeting can only be regenerated for scheduled or active sessions.",
        )

    try:
        from modules.integrations.video_meeting_service import create_meeting_for_booking

        # Get tutor profile for provider preferences
        tutor_profile = booking.tutor_profile
        if not tutor_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Booking has no associated tutor profile",
            )

        # Create meeting using tutor's preferred provider
        meeting_result = await create_meeting_for_booking(db, booking, tutor_profile)

        if meeting_result.success:
            # Update booking with new meeting details
            booking.join_url = meeting_result.join_url
            booking.meeting_url = meeting_result.host_url
            booking.video_provider = meeting_result.provider

            # Provider-specific fields
            if meeting_result.provider == "zoom" and meeting_result.meeting_id:
                booking.zoom_meeting_id = meeting_result.meeting_id
                booking.zoom_meeting_pending = False
            elif meeting_result.provider == "google_meet" and meeting_result.join_url:
                booking.google_meet_link = meeting_result.join_url

            booking.updated_at = datetime.now(UTC)
            db.commit()
            db.refresh(booking)

            logger.info(
                "Regenerated %s meeting for booking %d (requested by user %d)",
                meeting_result.provider,
                booking_id,
                current_user.id,
            )

            _add_booking_cache_headers(response, booking)
            return booking_to_dto(booking, db)

        else:
            logger.error(
                "Failed to regenerate meeting for booking %d using %s: %s",
                booking_id,
                meeting_result.provider,
                meeting_result.error_message,
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to create meeting: {meeting_result.error_message}. Please try again later.",
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Unexpected error regenerating meeting for booking %d: %s",
            booking_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate meeting: {str(e)}",
        )


# ============================================================================
# Session Attendance Tracking Endpoints
# ============================================================================


@router.post("/bookings/{booking_id}/join", response_model=BookingDTO)
async def record_session_join(
    booking_id: int,
    request: RecordJoinRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Record that the current user has joined the session.

    This endpoint tracks attendance for determining session outcomes when
    the session auto-ends. It should be called when a user clicks the
    "Join Session" button or enters the video call.

    - Can only join SCHEDULED or ACTIVE sessions
    - Tutors record tutor_joined_at
    - Students record student_joined_at
    - Idempotent: subsequent calls do not update the timestamp

    Attendance-based outcome determination:
    - Neither joined -> NOT_HELD (void payment)
    - Only student joined -> NO_SHOW_TUTOR (refund student)
    - Only tutor joined -> NO_SHOW_STUDENT (tutor earns payment)
    - Both joined -> COMPLETED (normal completion)
    """
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)

    # Validate booking state
    if booking.session_state not in [SessionState.SCHEDULED.value, SessionState.ACTIVE.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot join session with state {booking.session_state}. "
            "Sessions can only be joined when SCHEDULED or ACTIVE.",
        )

    try:
        now = datetime.now(UTC)
        updated = False

        # Determine which field to update based on user role
        if current_user.role == "tutor":
            # Verify this is the tutor for this booking
            tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == current_user.id).first()
            if not tutor_profile or booking.tutor_profile_id != tutor_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to join this session as tutor",
                )
            # Idempotent: only set if not already set
            if booking.tutor_joined_at is None:
                booking.tutor_joined_at = now
                updated = True
                logger.info(
                    "Tutor (user %d) joined session for booking %d at %s",
                    current_user.id,
                    booking_id,
                    now.isoformat(),
                )
        elif current_user.role == "student":
            # Verify this is the student for this booking
            if booking.student_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to join this session as student",
                )
            # Idempotent: only set if not already set
            if booking.student_joined_at is None:
                booking.student_joined_at = now
                updated = True
                logger.info(
                    "Student (user %d) joined session for booking %d at %s",
                    current_user.id,
                    booking_id,
                    now.isoformat(),
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tutors and students can join sessions",
            )

        if updated:
            booking.updated_at = now
            BookingStateMachine.increment_version(booking)
            db.commit()
            db.refresh(booking)

        _add_booking_cache_headers(response, booking)
        return booking_to_dto(booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to record session join for booking %d, user %d: %s",
            booking_id,
            current_user.id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record session join: {str(e)}",
        )
