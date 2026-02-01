"""Tutor availability API routes."""

import logging
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from core.dependencies import get_current_tutor_profile
from core.rate_limiting import limiter
from core.timezone import is_valid_timezone
from database import get_db
from models import Booking, TutorAvailability, TutorBlackout, TutorProfile
from schemas import (
    AvailableSlot,
    ConflictingBookingInfo,
    TutorAvailabilityCreate,
    TutorAvailabilityResponse,
    TutorBlackoutCreate,
    TutorBlackoutCreateResponse,
    TutorBlackoutResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutors", tags=["tutor-availability"])


@router.get("/{tutor_id}/available-slots", response_model=list[AvailableSlot])
@limiter.limit("60/minute")
async def get_available_slots(
    request: Request,
    tutor_id: int,
    start_date: str,
    end_date: str,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Get available time slots for a tutor within a date range.
    Returns 30-minute slots that are available based on tutor's recurring availability
    and existing bookings.

    Cache headers are set to suggest short cache times (30 seconds) to reduce stale data.
    The X-Slots-Generated-At header indicates when slots were computed.
    """
    # Set cache control headers to reduce stale slot data
    # Private: only browser cache (not CDN), max-age: 30 seconds
    response.headers["Cache-Control"] = "private, max-age=30"
    response.headers["X-Slots-Generated-At"] = datetime.now(UTC).isoformat()
    # Verify tutor exists and is approved
    tutor = db.query(TutorProfile).filter(TutorProfile.id == tutor_id, TutorProfile.is_approved.is_(True)).first()
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found or not approved")

    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    if (end_dt - start_dt).days > 30:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 30 days")

    # Get tutor's recurring availability
    availabilities = db.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == tutor_id).all()

    if not availabilities:
        return []

    # Get existing bookings that overlap the date range
    # Use session_state from the new booking state machine design
    bookings = (
        db.query(Booking)
        .filter(
            Booking.tutor_profile_id == tutor_id,
            Booking.session_state.in_(["REQUESTED", "SCHEDULED"]),
            Booking.start_time < end_dt,
            Booking.end_time > start_dt,
        )
        .all()
    )

    # Generate available slots
    available_slots = []
    current_date = start_dt.date()
    end_date_obj = end_dt.date()

    # Log availability configuration for debugging
    logger.debug(
        f"Tutor {tutor_id} has {len(availabilities)} availability rules: "
        f"{[(av.day_of_week, av.start_time, av.end_time) for av in availabilities]}"
    )

    while current_date <= end_date_obj:
        # Convert Python weekday (Mon=0, Sun=6) to JS convention (Sun=0, Sat=6)
        # This matches the frontend where Sunday=0, Monday=1, ..., Saturday=6
        python_weekday = current_date.weekday()  # Monday=0, Sunday=6
        day_of_week = (python_weekday + 1) % 7  # Convert to Sunday=0, Saturday=6

        # Find availability rules for this day
        day_availabilities = [av for av in availabilities if av.day_of_week == day_of_week]

        if day_availabilities:
            logger.debug(
                f"Date {current_date} ({current_date.strftime('%A')}) -> "
                f"Python weekday={python_weekday}, JS day_of_week={day_of_week}, "
                f"found {len(day_availabilities)} matching rules"
            )

        for availability in day_availabilities:
            # Generate 30-minute slots within availability window
            slot_start_time = availability.start_time
            slot_end_time = availability.end_time

            # Get the timezone for this availability slot (DST-safe)
            # This ensures proper UTC conversion even during DST transitions
            avail_tz_str = getattr(availability, 'timezone', None) or "UTC"
            if not is_valid_timezone(avail_tz_str):
                avail_tz_str = "UTC"
            avail_tz = ZoneInfo(avail_tz_str)

            # Convert time to datetime in the tutor's timezone first, then to UTC
            # This handles DST correctly - e.g., 9am EST becomes different UTC times
            # depending on whether DST is in effect on that specific date
            local_start = datetime.combine(current_date, slot_start_time)
            local_end = datetime.combine(current_date, slot_end_time)

            # Localize to tutor's timezone (this applies correct DST offset for the date)
            local_start_aware = local_start.replace(tzinfo=avail_tz)
            local_end_aware = local_end.replace(tzinfo=avail_tz)

            # Convert to UTC for consistent comparison with bookings
            current_slot = local_start_aware.astimezone(ZoneInfo("UTC"))
            end_boundary = local_end_aware.astimezone(ZoneInfo("UTC"))

            while current_slot + timedelta(minutes=30) <= end_boundary:
                slot_end = current_slot + timedelta(minutes=30)

                # Skip past slots (use UTC for comparison)
                now_utc = datetime.now(UTC)
                if current_slot < now_utc:
                    current_slot = slot_end
                    continue

                # Check if slot conflicts with existing bookings (both are now timezone-aware)
                is_booked = any(
                    booking.start_time < slot_end and booking.end_time > current_slot for booking in bookings
                )

                if not is_booked:
                    available_slots.append(
                        {
                            "start_time": current_slot.isoformat(),
                            "end_time": slot_end.isoformat(),
                            "duration_minutes": 30,
                        }
                    )

                current_slot = slot_end

        current_date += timedelta(days=1)

    return available_slots


@router.get("/availability", response_model=list[TutorAvailabilityResponse])
@limiter.limit("60/minute")
async def get_my_availability(
    request: Request,
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """Get current tutor's availability schedule."""
    availabilities = (
        db.query(TutorAvailability)
        .filter(TutorAvailability.tutor_profile_id == profile.id)
        .order_by(TutorAvailability.day_of_week, TutorAvailability.start_time)
        .all()
    )

    return availabilities


@router.post(
    "/availability",
    response_model=TutorAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def create_availability(
    request: Request,
    availability_data: TutorAvailabilityCreate,
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """Create new availability slot for current tutor."""

    # Validate time range
    if availability_data.start_time >= availability_data.end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time")

    # Check for overlapping availability on the same day
    # Two time ranges overlap if: start1 < end2 AND end1 > start2
    overlapping = (
        db.query(TutorAvailability)
        .filter(
            TutorAvailability.tutor_profile_id == profile.id,
            TutorAvailability.day_of_week == availability_data.day_of_week,
            TutorAvailability.start_time < availability_data.end_time,
            TutorAvailability.end_time > availability_data.start_time,
        )
        .first()
    )

    if overlapping:
        raise HTTPException(
            status_code=400,
            detail=f"New availability overlaps with existing window: {overlapping.start_time.strftime('%H:%M')}-{overlapping.end_time.strftime('%H:%M')}",
        )

    try:
        # Use tutor's profile timezone for the availability slot
        # This ensures proper DST handling when generating available slots
        tutor_timezone = profile.timezone or profile.user.timezone or "UTC"

        availability = TutorAvailability(
            tutor_profile_id=profile.id,
            day_of_week=availability_data.day_of_week,
            start_time=availability_data.start_time,
            end_time=availability_data.end_time,
            is_recurring=availability_data.is_recurring,
            timezone=tutor_timezone,
        )
        db.add(availability)
        db.commit()
        db.refresh(availability)

        logger.info(
            f"Availability created for tutor profile {profile.id}: "
            f"Day {availability_data.day_of_week}, "
            f"{availability_data.start_time}-{availability_data.end_time} "
            f"(timezone: {tutor_timezone})"
        )
        return availability
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to create availability") from e


@router.delete("/availability/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_availability(
    request: Request,
    availability_id: int,
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """Delete availability slot."""
    availability = (
        db.query(TutorAvailability)
        .filter(
            TutorAvailability.id == availability_id,
            TutorAvailability.tutor_profile_id == profile.id,
        )
        .first()
    )

    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")

    try:
        db.delete(availability)
        db.commit()
        logger.info(f"Availability {availability_id} deleted by tutor {profile.user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete availability") from e


@router.post("/availability/bulk", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_bulk_availability(
    request: Request,
    availabilities: list[TutorAvailabilityCreate],
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """Create multiple availability slots at once."""

    if len(availabilities) > 50:
        raise HTTPException(status_code=400, detail="Cannot create more than 50 slots at once")

    # Validate no overlaps within the new availability entries
    # Group by day_of_week and check for overlaps within each day
    valid_slots: list[TutorAvailabilityCreate] = []
    for av_data in availabilities:
        if av_data.start_time >= av_data.end_time:
            continue  # Skip invalid slots (start_time must be before end_time)
        valid_slots.append(av_data)

    # Check for overlaps within the new entries (same day)
    for i, slot1 in enumerate(valid_slots):
        for slot2 in valid_slots[i + 1 :]:
            # Two time ranges overlap if: same day AND start1 < end2 AND end1 > start2
            if slot1.day_of_week == slot2.day_of_week and slot1.start_time < slot2.end_time and slot1.end_time > slot2.start_time:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Overlapping availability windows on day {slot1.day_of_week}: "
                        f"{slot1.start_time.strftime('%H:%M')}-{slot1.end_time.strftime('%H:%M')} "
                        f"overlaps with {slot2.start_time.strftime('%H:%M')}-{slot2.end_time.strftime('%H:%M')}",
                    )

    # Clear existing availability
    db.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == profile.id).delete()

    # Use tutor's profile timezone for all availability slots
    tutor_timezone = profile.timezone or profile.user.timezone or "UTC"

    created_slots = []
    skipped_count = len(availabilities) - len(valid_slots)
    try:
        for av_data in valid_slots:

            availability = TutorAvailability(
                tutor_profile_id=profile.id,
                day_of_week=av_data.day_of_week,
                start_time=av_data.start_time,
                end_time=av_data.end_time,
                is_recurring=av_data.is_recurring,
                timezone=tutor_timezone,
            )
            db.add(availability)
            created_slots.append(availability)

        db.commit()
        logger.info(f"Bulk availability created for tutor profile {profile.id}: {len(created_slots)} slots, {skipped_count} skipped")
        return {
            "message": f"Successfully created {len(created_slots)} availability slots",
            "count": len(created_slots),
            "skipped": skipped_count,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating bulk availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to create bulk availability") from e


# ============================================================================
# Blackout Period Endpoints
# ============================================================================


@router.get("/blackouts", response_model=list[TutorBlackoutResponse])
@limiter.limit("60/minute")
async def get_my_blackouts(
    request: Request,
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """Get current tutor's blackout periods."""
    blackouts = (
        db.query(TutorBlackout)
        .filter(TutorBlackout.tutor_id == profile.user_id)
        .order_by(TutorBlackout.start_at.desc())
        .all()
    )
    return blackouts


@router.post(
    "/blackouts",
    response_model=TutorBlackoutCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def create_blackout(
    request: Request,
    blackout_data: TutorBlackoutCreate,
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """
    Create a new blackout period (unavailable time) for the current tutor.

    This endpoint will:
    1. Create the blackout period
    2. Check for any existing REQUESTED or SCHEDULED bookings during that time
    3. Return a warning if conflicting bookings exist (tutor should cancel/reschedule them)

    The blackout is created regardless of conflicts - the warning is informational.
    """
    # Validate time range
    if blackout_data.end_datetime <= blackout_data.start_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Check for overlapping blackout periods
    overlapping_blackout = (
        db.query(TutorBlackout)
        .filter(
            TutorBlackout.tutor_id == profile.user_id,
            TutorBlackout.start_at < blackout_data.end_datetime,
            TutorBlackout.end_at > blackout_data.start_datetime,
        )
        .first()
    )

    if overlapping_blackout:
        raise HTTPException(
            status_code=409,
            detail="This blackout period overlaps with an existing blackout",
        )

    # Check for conflicting bookings (REQUESTED or SCHEDULED sessions)
    conflicting_bookings = (
        db.query(Booking)
        .filter(
            Booking.tutor_profile_id == profile.id,
            Booking.session_state.in_(["REQUESTED", "SCHEDULED"]),
            Booking.start_time < blackout_data.end_datetime,
            Booking.end_time > blackout_data.start_datetime,
        )
        .all()
    )

    try:
        # Create the blackout period
        blackout = TutorBlackout(
            tutor_id=profile.user_id,
            start_at=blackout_data.start_datetime,
            end_at=blackout_data.end_datetime,
            reason=blackout_data.reason,
        )
        db.add(blackout)
        db.commit()
        db.refresh(blackout)

        logger.info(
            f"Blackout created for tutor {profile.user_id}: "
            f"{blackout_data.start_datetime} to {blackout_data.end_datetime}"
        )

        # Build response with blackout data
        blackout_response = TutorBlackoutResponse(
            id=blackout.id,
            tutor_id=blackout.tutor_id,
            start_at=blackout.start_at,
            end_at=blackout.end_at,
            reason=blackout.reason,
            created_at=blackout.created_at,
        )

        # Build warning response if there are conflicting bookings
        if conflicting_bookings:
            conflicting_info = [
                ConflictingBookingInfo(
                    id=b.id,
                    start_time=b.start_time,
                    end_time=b.end_time,
                    session_state=b.session_state,
                    student_name=b.student_name,
                    subject_name=b.subject_name,
                )
                for b in conflicting_bookings
            ]

            logger.warning(
                f"Blackout created with {len(conflicting_bookings)} conflicting bookings "
                f"for tutor {profile.user_id}"
            )

            return TutorBlackoutCreateResponse(
                blackout=blackout_response,
                warning=f"You have {len(conflicting_bookings)} existing booking(s) during this blackout period",
                conflicting_bookings=conflicting_info,
                action_required="Please cancel or reschedule these bookings to avoid missed sessions",
            )

        return TutorBlackoutCreateResponse(blackout=blackout_response)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating blackout: {e}")
        raise HTTPException(status_code=500, detail="Failed to create blackout period") from e


@router.delete("/blackouts/{blackout_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
async def delete_blackout(
    request: Request,
    blackout_id: int,
    profile: TutorProfile = Depends(get_current_tutor_profile),
    db: Session = Depends(get_db),
):
    """Delete a blackout period."""
    blackout = (
        db.query(TutorBlackout)
        .filter(
            TutorBlackout.id == blackout_id,
            TutorBlackout.tutor_id == profile.user_id,
        )
        .first()
    )

    if not blackout:
        raise HTTPException(status_code=404, detail="Blackout period not found")

    try:
        db.delete(blackout)
        db.commit()
        logger.info(f"Blackout {blackout_id} deleted by tutor {profile.user.email}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting blackout: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete blackout period") from e
