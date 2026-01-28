"""Tutor availability API routes."""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from core.dependencies import get_current_tutor_profile
from core.rate_limiting import limiter
from database import get_db
from models import Booking, TutorAvailability, TutorProfile
from schemas import AvailableSlot, TutorAvailabilityCreate, TutorAvailabilityResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutors", tags=["tutor-availability"])


@router.get("/{tutor_id}/available-slots", response_model=list[AvailableSlot])
@limiter.limit("60/minute")
async def get_available_slots(
    request: Request,
    tutor_id: int,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
):
    """
    Get available time slots for a tutor within a date range.
    Returns 30-minute slots that are available based on tutor's recurring availability
    and existing bookings.
    """
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
    bookings = (
        db.query(Booking)
        .filter(
            Booking.tutor_profile_id == tutor_id,
            Booking.status.in_(["PENDING", "CONFIRMED"]),
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

            # Convert time to datetime for the specific date (UTC-aware)
            current_slot = datetime.combine(current_date, slot_start_time).replace(tzinfo=UTC)
            end_boundary = datetime.combine(current_date, slot_end_time).replace(tzinfo=UTC)

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
    overlapping = (
        db.query(TutorAvailability)
        .filter(
            TutorAvailability.tutor_profile_id == profile.id,
            TutorAvailability.day_of_week == availability_data.day_of_week,
            or_(
                and_(
                    TutorAvailability.start_time <= availability_data.start_time,
                    TutorAvailability.end_time > availability_data.start_time,
                ),
                and_(
                    TutorAvailability.start_time < availability_data.end_time,
                    TutorAvailability.end_time >= availability_data.end_time,
                ),
                and_(
                    TutorAvailability.start_time >= availability_data.start_time,
                    TutorAvailability.end_time <= availability_data.end_time,
                ),
            ),
        )
        .first()
    )

    if overlapping:
        raise HTTPException(
            status_code=409,
            detail="This time slot overlaps with existing availability",
        )

    try:
        availability = TutorAvailability(
            tutor_profile_id=profile.id,
            day_of_week=availability_data.day_of_week,
            start_time=availability_data.start_time,
            end_time=availability_data.end_time,
            is_recurring=availability_data.is_recurring,
        )
        db.add(availability)
        db.commit()
        db.refresh(availability)

        logger.info(
            f"Availability created for tutor profile {profile.id}: "
            f"Day {availability_data.day_of_week}, "
            f"{availability_data.start_time}-{availability_data.end_time}"
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

    # Clear existing availability
    db.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == profile.id).delete()

    created_slots = []
    skipped_count = 0
    try:
        for av_data in availabilities:
            if av_data.start_time >= av_data.end_time:
                skipped_count += 1
                continue  # Skip invalid slots (start_time must be before end_time)

            availability = TutorAvailability(
                tutor_profile_id=profile.id,
                day_of_week=av_data.day_of_week,
                start_time=av_data.start_time,
                end_time=av_data.end_time,
                is_recurring=av_data.is_recurring,
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
