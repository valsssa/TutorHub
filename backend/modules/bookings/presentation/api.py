"""
Clean booking API endpoints following presentation layer pattern.
Consolidates all booking routes with shared error handling and authorization.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from core.dependencies import get_current_tutor_profile, get_current_user
from database import get_db
from models import Booking, TutorProfile, User
from modules.bookings.policy_engine import ReschedulePolicy
from modules.bookings.domain.state_machine import BookingStateMachine
from modules.bookings.domain.status import DisputeState, SessionState
from modules.bookings.schemas import (
    BookingCancelRequest,
    BookingConfirmRequest,
    BookingCreateRequest,
    BookingDeclineRequest,
    BookingDTO,
    BookingListResponse,
    BookingRescheduleRequest,
    DisputeCreateRequest,
    DisputeResolveRequest,
    MarkNoShowRequest,
)
from modules.bookings.service import BookingService, booking_to_dto

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["bookings"])


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


def _require_role(current_user: User, role: str) -> None:
    """Ensure user has specific role."""
    if current_user.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {role}s can access this endpoint",
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create tutoring session booking with automatic conflict checking and pricing.

    - Validates tutor availability and checks for conflicts
    - Calculates pricing with platform fee
    - Auto-confirms if tutor has auto_confirm enabled
    - Deducts package credit if package_id provided
    """
    _require_role(current_user, "student")

    try:
        from modules.bookings.services.response_tracking import ResponseTrackingService

        service = BookingService(db)
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

        return booking_to_dto(booking, db)

    except HTTPException:
        raise
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
                Booking.start_time >= datetime.utcnow(),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed booking information with authorization check."""
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)
    return booking_to_dto(booking, db)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingDTO)
async def cancel_booking(
    booking_id: int,
    request: BookingCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Cancel booking with refund policy enforcement.

    - Students and tutors can cancel their bookings
    - Refund policy: >= 12h before = full refund, < 12h = no refund
    - Restores package credit if applicable
    """
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)

    try:
        service = BookingService(db)
        cancelled_booking = service.cancel_booking(
            booking=booking,
            cancelled_by_role=current_user.role.upper(),
            reason=request.reason,
        )

        db.commit()
        db.refresh(cancelled_booking)

        await _broadcast_availability_update(
            tutor_profile_id=cancelled_booking.tutor_profile_id,
            tutor_user_id=cancelled_booking.tutor_profile.user_id if cancelled_booking.tutor_profile else 0,
        )

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reschedule booking to new time (student only).

    - Must be >= 12h before original time
    - Checks new time for tutor availability conflicts
    """
    _require_role(current_user, "student")

    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.student_id == current_user.id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    try:
        service = BookingService(db)

        # Validate reschedule timing
        decision = ReschedulePolicy.evaluate_reschedule(
            booking_start_at=booking.start_time,
            now=datetime.utcnow(),
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

        # Check conflicts at new time
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
                    detail=f"Tutor not available at new time: {conflicts}",
                )

        # Update booking
        booking.start_time = request.new_start_at
        booking.end_time = new_end_at
        booking.notes = (booking.notes or "") + f"\n[Rescheduled at {datetime.utcnow()}]"

        db.commit()
        db.refresh(booking)

        await _broadcast_availability_update(
            tutor_profile_id=booking.tutor_profile_id,
            tutor_user_id=booking.tutor_profile.user_id if booking.tutor_profile else 0,
        )

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
    tutor_profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Confirm pending booking (tutor only).

    - Changes status from PENDING to CONFIRMED
    - Generates meeting join URL
    """
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

    # Use state machine to validate and transition
    result = BookingStateMachine.accept_booking(booking)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message or f"Cannot confirm booking with state {booking.session_state}",
        )

    try:
        from datetime import datetime

        from modules.bookings.services.response_tracking import ResponseTrackingService

        # Generate join URL
        service = BookingService(db)
        booking.join_url = service._generate_join_url(booking.id)

        # Add tutor notes
        if request.notes_tutor:
            booking.notes_tutor = request.notes_tutor

        # Update timestamp in application code (no DB triggers)
        booking.updated_at = datetime.now(UTC)

        # Track response time
        response_tracker = ResponseTrackingService(db)
        response_tracker.log_tutor_response(booking, "confirmed")

        db.commit()
        db.refresh(booking)

        await _broadcast_availability_update(
            tutor_profile_id=booking.tutor_profile_id,
            tutor_user_id=tutor_profile.user_id,
        )

        return booking_to_dto(booking, db)

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
    tutor_profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Decline pending booking (tutor only).

    - Changes status to CANCELLED_BY_TUTOR
    - Automatically refunds student
    """
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
        from modules.bookings.services.response_tracking import ResponseTrackingService

        service = BookingService(db)
        declined_booking = service.cancel_booking(
            booking=booking,
            cancelled_by_role="TUTOR",
            reason=request.reason,
        )

        # Track response time
        response_tracker = ResponseTrackingService(db)
        response_tracker.log_tutor_response(booking, "cancelled")

        db.commit()
        db.refresh(declined_booking)

        await _broadcast_availability_update(
            tutor_profile_id=declined_booking.tutor_profile_id,
            tutor_user_id=tutor_profile.user_id,
        )

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
    tutor_profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Mark student as no-show (tutor only).

    - Must be 10+ minutes after start time and within 24h
    - Tutor earns full payment
    """
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
        service = BookingService(db)
        no_show_booking = service.mark_no_show(
            booking=booking,
            reporter_role="TUTOR",
            notes=request.notes,
        )

        db.commit()
        db.refresh(no_show_booking)

        return booking_to_dto(no_show_booking, db)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark tutor as no-show (student only).

    - Must be 10+ minutes after start time and within 24h
    - Student receives full refund
    """
    _require_role(current_user, "student")

    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.student_id == current_user.id,
        )
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    try:
        service = BookingService(db)
        no_show_booking = service.mark_no_show(
            booking=booking,
            reporter_role="STUDENT",
            notes=request.notes,
        )

        db.commit()
        db.refresh(no_show_booking)

        return booking_to_dto(no_show_booking, db)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Open a dispute on a booking (student or tutor).

    - Can only dispute bookings in terminal states (ENDED, CANCELLED, EXPIRED)
    - Cannot dispute if already has an open dispute
    """
    booking = _get_booking_or_404(booking_id, db, current_user=current_user, verify_ownership=True)

    try:
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
        db.commit()
        db.refresh(booking)

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Resolve a dispute (admin only).

    - Resolves to RESOLVED_UPHELD (original decision stands) or RESOLVED_REFUNDED (refund granted)
    - Can issue full or partial refund
    """
    # Require admin role
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can resolve disputes",
        )

    booking = _get_booking_or_404(booking_id, db, current_user=None, verify_ownership=False)

    try:
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

        booking.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(booking)

        return booking_to_dto(booking, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve dispute: {str(e)}",
        )
