"""
Availability Service Tests

Tests for tutor availability management, scheduling, conflict detection, and timezone handling.
"""

import pytest
from datetime import datetime, date, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.models.tutors import TutorAvailability, TutorBlackout
from backend.modules.tutor_profile.application.services import AvailabilityService


@pytest.fixture
def availability_monday_9to5():
    """Monday 9am-5pm availability"""
    return {
        "day_of_week": 1,  # Monday
        "start_time": time(9, 0),
        "end_time": time(17, 0)
    }


@pytest.fixture
def blackout_holiday_week():
    """Holiday week blackout"""
    return {
        "start_time": datetime(2025, 12, 20, 0, 0, 0, tzinfo=dt_timezone.utc),
        "end_time": datetime(2025, 12, 27, 23, 59, 59, tzinfo=dt_timezone.utc),
        "reason": "Holiday vacation"
    }


class TestAvailabilityCreation:
    """Test creating recurring availability slots"""

    def test_create_single_availability_slot(self, db: Session, test_tutor_profile):
        """Test creating single availability slot"""
        # Given
        slot = {
            "day_of_week": 1,  # Monday
            "start_time": time(9, 0),
            "end_time": time(17, 0)
        }

        # When
        created = AvailabilityService.add_slot(db, test_tutor_profile.id, slot)

        # Then
        assert created.day_of_week == 1
        assert created.start_time == time(9, 0)
        assert created.end_time == time(17, 0)
        assert created.tutor_profile_id == test_tutor_profile.id

    def test_create_multiple_availability_slots(self, db: Session, test_tutor_profile):
        """Test creating availability for multiple days"""
        # Given
        slots = [
            {"day_of_week": 1, "start_time": time(9, 0), "end_time": time(17, 0)},  # Mon
            {"day_of_week": 3, "start_time": time(10, 0), "end_time": time(16, 0)},  # Wed
            {"day_of_week": 5, "start_time": time(14, 0), "end_time": time(20, 0)}   # Fri
        ]

        # When
        created_slots = AvailabilityService.set_availability(
            db,
            test_tutor_profile.id,
            slots
        )

        # Then
        assert len(created_slots) == 3
        assert created_slots[0].day_of_week == 1
        assert created_slots[1].day_of_week == 3
        assert created_slots[2].day_of_week == 5

    def test_create_availability_full_week(self, db: Session, test_tutor_profile):
        """Test creating availability Mon-Fri"""
        # Given
        slots = [
            {"day_of_week": day, "start_time": time(9, 0), "end_time": time(17, 0)}
            for day in range(1, 6)  # Monday(1) to Friday(5)
        ]

        # When
        created_slots = AvailabilityService.set_availability(
            db,
            test_tutor_profile.id,
            slots
        )

        # Then
        assert len(created_slots) == 5
        # Verify all weekdays covered
        days = [slot.day_of_week for slot in created_slots]
        assert sorted(days) == [1, 2, 3, 4, 5]


class TestAvailabilityValidation:
    """Test availability validation rules"""

    def test_availability_overlap_same_day_error(self, db: Session, test_tutor_profile):
        """Test error on overlapping slots on same day"""
        # Given - existing slot Mon 9am-5pm
        existing = TutorAvailability(
            tutor_profile_id=test_tutor_profile.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        db.add(existing)
        db.commit()

        # When - try to add Mon 3pm-7pm (overlaps)
        with pytest.raises(ValueError, match="Overlapping availability"):
            AvailabilityService.add_slot(
                db,
                test_tutor_profile.id,
                {"day_of_week": 1, "start_time": time(15, 0), "end_time": time(19, 0)}
            )

    def test_availability_adjacent_slots_allowed(self, db: Session, test_tutor_profile):
        """Test that adjacent slots (no overlap) are allowed"""
        # Given - existing slot Mon 9am-1pm
        existing = TutorAvailability(
            tutor_profile_id=test_tutor_profile.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(13, 0)
        )
        db.add(existing)
        db.commit()

        # When - add Mon 1pm-5pm (exactly adjacent, no overlap)
        created = AvailabilityService.add_slot(
            db,
            test_tutor_profile.id,
            {"day_of_week": 1, "start_time": time(13, 0), "end_time": time(17, 0)}
        )

        # Then - should succeed
        assert created.start_time == time(13, 0)

    def test_availability_end_before_start_error(self, db: Session, test_tutor_profile):
        """Test error when end_time is before start_time"""
        # When/Then
        with pytest.raises(ValueError, match="End time must be after start time"):
            AvailabilityService.add_slot(
                db,
                test_tutor_profile.id,
                {"day_of_week": 1, "start_time": time(17, 0), "end_time": time(9, 0)}
            )

    def test_availability_invalid_day_of_week(self, db: Session, test_tutor_profile):
        """Test error on invalid day_of_week (0-6 valid)"""
        # When/Then
        with pytest.raises(ValueError, match="Invalid day of week"):
            AvailabilityService.add_slot(
                db,
                test_tutor_profile.id,
                {"day_of_week": 8, "start_time": time(9, 0), "end_time": time(17, 0)}
            )

    def test_availability_minimum_duration(self, db: Session, test_tutor_profile):
        """Test minimum slot duration (e.g., 30 minutes)"""
        # When/Then - try 15 minute slot
        with pytest.raises(ValueError, match="Minimum duration"):
            AvailabilityService.add_slot(
                db,
                test_tutor_profile.id,
                {"day_of_week": 1, "start_time": time(9, 0), "end_time": time(9, 15)}
            )


class TestAvailabilityUpdates:
    """Test updating existing availability"""

    def test_update_availability_slot(self, db: Session, test_tutor_availability):
        """Test updating existing slot times"""
        # Given - existing Mon 9am-5pm
        slot_id = test_tutor_availability.id

        # When - change to 10am-4pm
        updated = AvailabilityService.update_slot(
            db,
            slot_id,
            {"start_time": time(10, 0), "end_time": time(16, 0)}
        )

        # Then
        assert updated.start_time == time(10, 0)
        assert updated.end_time == time(16, 0)

    def test_delete_availability_slot(self, db: Session, test_tutor_availability):
        """Test deleting availability slot"""
        # Given
        slot_id = test_tutor_availability.id

        # When
        AvailabilityService.delete_slot(db, slot_id)

        # Then
        deleted_slot = db.query(TutorAvailability).filter_by(id=slot_id).first()
        assert deleted_slot is None

    def test_delete_availability_with_future_bookings_error(
        self,
        db: Session,
        test_tutor_availability,
        test_booking_confirmed
    ):
        """Test error when deleting slot with confirmed future bookings"""
        # Given - availability slot with future confirmed booking
        slot_id = test_tutor_availability.id

        # When/Then
        with pytest.raises(ValueError, match="Cannot delete.*confirmed bookings"):
            AvailabilityService.delete_slot(db, slot_id, check_bookings=True)

    def test_replace_all_availability(self, db: Session, test_tutor_profile_with_availability):
        """Test replacing entire availability schedule"""
        # Given - profile has existing availability
        profile_id = test_tutor_profile_with_availability.id
        assert len(test_tutor_profile_with_availability.availabilities) > 0

        # When - replace with new schedule
        new_schedule = [
            {"day_of_week": 2, "start_time": time(13, 0), "end_time": time(18, 0)},  # Tue
            {"day_of_week": 4, "start_time": time(10, 0), "end_time": time(15, 0)}   # Thu
        ]
        result = AvailabilityService.set_availability(db, profile_id, new_schedule)

        # Then
        assert len(result) == 2
        days = [slot.day_of_week for slot in result]
        assert sorted(days) == [2, 4]


class TestBlackoutPeriods:
    """Test blackout/vacation period management"""

    def test_create_blackout_period(self, db: Session, test_tutor_profile, blackout_holiday_week):
        """Test creating blackout period"""
        # When
        created = AvailabilityService.create_blackout(
            db,
            test_tutor_profile.id,
            blackout_holiday_week
        )

        # Then
        assert created.tutor_profile_id == test_tutor_profile.id
        assert created.reason == "Holiday vacation"
        assert created.start_time.year == 2025
        assert created.start_time.month == 12

    def test_create_multiple_blackouts(self, db: Session, test_tutor_profile):
        """Test creating multiple non-overlapping blackout periods"""
        # Given
        blackout1 = {
            "start_time": datetime(2025, 7, 1, tzinfo=dt_timezone.utc),
            "end_time": datetime(2025, 7, 7, tzinfo=dt_timezone.utc),
            "reason": "Summer break"
        }
        blackout2 = {
            "start_time": datetime(2025, 12, 20, tzinfo=dt_timezone.utc),
            "end_time": datetime(2025, 12, 27, tzinfo=dt_timezone.utc),
            "reason": "Winter holidays"
        }

        # When
        created1 = AvailabilityService.create_blackout(db, test_tutor_profile.id, blackout1)
        created2 = AvailabilityService.create_blackout(db, test_tutor_profile.id, blackout2)

        # Then
        assert created1.id != created2.id
        assert len(test_tutor_profile.blackouts) == 2

    def test_blackout_overlapping_error(self, db: Session, test_tutor_profile):
        """Test error when creating overlapping blackout periods"""
        # Given - existing blackout Dec 20-27
        existing = TutorBlackout(
            tutor_profile_id=test_tutor_profile.id,
            start_time=datetime(2025, 12, 20, tzinfo=dt_timezone.utc),
            end_time=datetime(2025, 12, 27, tzinfo=dt_timezone.utc),
            reason="Existing"
        )
        db.add(existing)
        db.commit()

        # When - try to add Dec 23-30 (overlaps)
        with pytest.raises(ValueError, match="Overlapping blackout"):
            AvailabilityService.create_blackout(
                db,
                test_tutor_profile.id,
                {
                    "start_time": datetime(2025, 12, 23, tzinfo=dt_timezone.utc),
                    "end_time": datetime(2025, 12, 30, tzinfo=dt_timezone.utc),
                    "reason": "New"
                }
            )

    def test_delete_blackout(self, db: Session, test_tutor_blackout):
        """Test deleting blackout period"""
        # Given
        blackout_id = test_tutor_blackout.id

        # When
        AvailabilityService.delete_blackout(db, blackout_id)

        # Then
        deleted = db.query(TutorBlackout).filter_by(id=blackout_id).first()
        assert deleted is None


class TestAvailableSlotRetrieval:
    """Test retrieving available time slots for booking"""

    def test_get_available_slots_for_date(
        self,
        db: Session,
        test_tutor_profile_with_availability
    ):
        """Test retrieving available slots for a specific date"""
        # Given - Monday with 9am-5pm availability
        monday = date(2025, 2, 3)  # A Monday

        # When
        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile_with_availability.id,
            monday,
            duration_minutes=60
        )

        # Then
        assert len(slots) > 0
        # Should return hourly slots from 9am to 4pm (last slot starts at 4pm)
        assert any(slot["start_time"].hour == 9 for slot in slots)
        assert any(slot["start_time"].hour == 16 for slot in slots)

    def test_available_slots_exclude_booked_times(
        self,
        db: Session,
        test_tutor_profile,
        test_booking_confirmed
    ):
        """Test that booked slots are excluded from available slots"""
        # Given - confirmed booking on a specific date/time
        booking_date = test_booking_confirmed.start_time.date()
        booking_hour = test_booking_confirmed.start_time.hour

        # When
        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile.id,
            booking_date,
            duration_minutes=60
        )

        # Then - booked hour should not be in available slots
        available_hours = [slot["start_time"].hour for slot in slots]
        assert booking_hour not in available_hours

    def test_available_slots_exclude_blackout_dates(
        self,
        db: Session,
        test_tutor_profile_with_blackout
    ):
        """Test that blackout dates have no available slots"""
        # Given - blackout period Dec 20-27
        blackout_date = date(2025, 12, 23)  # Within blackout

        # When
        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile_with_blackout.id,
            blackout_date,
            duration_minutes=60
        )

        # Then
        assert len(slots) == 0

    def test_available_slots_with_buffer_time(
        self,
        db: Session,
        test_tutor_profile,
        test_booking_confirmed
    ):
        """Test that buffer time (5 min) is enforced around bookings"""
        # Given - booking from 10:00-11:00
        # Buffer means 9:55-11:05 is blocked
        booking_date = test_booking_confirmed.start_time.date()

        # When
        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile.id,
            booking_date,
            duration_minutes=60,
            buffer_minutes=5
        )

        # Then - 9:00-10:00 and 11:00-12:00 slots should not be available
        # Only slots before 9:55 or after 11:05 available
        for slot in slots:
            slot_end = slot["end_time"]
            booking_start_with_buffer = test_booking_confirmed.start_time - timedelta(minutes=5)
            booking_end_with_buffer = test_booking_confirmed.end_time + timedelta(minutes=5)

            # Slot should not overlap with buffered booking time
            assert not (
                slot["start_time"] < booking_end_with_buffer and
                slot_end > booking_start_with_buffer
            )

    def test_no_slots_for_day_without_availability(
        self,
        db: Session,
        test_tutor_profile_with_availability
    ):
        """Test that days without set availability return no slots"""
        # Given - availability only on Monday
        # When - query for Tuesday (no availability)
        tuesday = date(2025, 2, 4)  # A Tuesday

        slots = AvailabilityService.get_available_slots(
            db,
            test_tutor_profile_with_availability.id,
            tuesday,
            duration_minutes=60
        )

        # Then
        assert len(slots) == 0


class TestTimezoneHandling:
    """Test timezone-aware availability and booking"""

    def test_availability_stored_in_tutor_timezone(self, db: Session, test_tutor_profile):
        """Test that availability is stored relative to tutor's timezone"""
        # Given - tutor in America/New_York (EST)
        test_tutor_profile.timezone = "America/New_York"
        db.commit()

        # When - set availability 9am-5pm (in tutor's local time)
        slot = AvailabilityService.add_slot(
            db,
            test_tutor_profile.id,
            {"day_of_week": 1, "start_time": time(9, 0), "end_time": time(17, 0)}
        )

        # Then - stored as naive time (will be interpreted in tutor's TZ)
        assert slot.start_time == time(9, 0)
        assert slot.end_time == time(17, 0)

    def test_convert_availability_to_student_timezone(self, db: Session, test_tutor_profile):
        """Test converting tutor availability to student's timezone"""
        # Given
        # - Tutor in America/New_York (UTC-5), available Mon 9am-5pm EST
        # - Student in Europe/London (UTC+0)
        test_tutor_profile.timezone = "America/New_York"
        db.commit()

        slot = TutorAvailability(
            tutor_profile_id=test_tutor_profile.id,
            day_of_week=1,  # Monday
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        db.add(slot)
        db.commit()

        # When - convert to London time (5 hours ahead)
        tutor_tz = ZoneInfo(test_tutor_profile.timezone)
        student_tz = ZoneInfo("Europe/London")

        # Create datetime in tutor's timezone
        monday = date(2025, 2, 3)
        tutor_start = datetime.combine(monday, slot.start_time, tzinfo=tutor_tz)
        tutor_end = datetime.combine(monday, slot.end_time, tzinfo=tutor_tz)

        # Convert to student timezone
        student_start = tutor_start.astimezone(student_tz)
        student_end = tutor_end.astimezone(student_tz)

        # Then - student sees 2pm-10pm GMT
        assert student_start.hour == 14  # 2pm
        assert student_end.hour == 22    # 10pm

    def test_booking_stored_in_utc(self, db: Session, test_booking_confirmed):
        """Test that bookings are always stored in UTC"""
        # Then
        assert test_booking_confirmed.start_time.tzinfo == dt_timezone.utc
        assert test_booking_confirmed.end_time.tzinfo == dt_timezone.utc


class TestAvailabilityConflictDetection:
    """Test conflict detection for booking attempts"""

    def test_detect_booking_conflict_same_time(
        self,
        db: Session,
        test_tutor_profile,
        test_booking_confirmed
    ):
        """Test detecting conflict with existing booking at exact same time"""
        # Given - booking from 10:00-11:00

        # When - check if 10:00-11:00 is available
        conflicts = AvailabilityService.check_booking_conflicts(
            db,
            test_tutor_profile.id,
            test_booking_confirmed.start_time,
            test_booking_confirmed.end_time
        )

        # Then
        assert len(conflicts) > 0

    def test_detect_booking_conflict_partial_overlap(
        self,
        db: Session,
        test_tutor_profile,
        test_booking_confirmed
    ):
        """Test detecting conflict with partial time overlap"""
        # Given - existing booking 10:00-11:00

        # When - try to book 10:30-11:30 (overlaps)
        conflict_start = test_booking_confirmed.start_time + timedelta(minutes=30)
        conflict_end = test_booking_confirmed.end_time + timedelta(minutes=30)

        conflicts = AvailabilityService.check_booking_conflicts(
            db,
            test_tutor_profile.id,
            conflict_start,
            conflict_end
        )

        # Then
        assert len(conflicts) > 0

    def test_no_conflict_adjacent_bookings(
        self,
        db: Session,
        test_tutor_profile,
        test_booking_confirmed
    ):
        """Test no conflict when bookings are back-to-back (with buffer)"""
        # Given - existing booking 10:00-11:00

        # When - book 11:05-12:05 (respecting 5-min buffer)
        new_start = test_booking_confirmed.end_time + timedelta(minutes=5)
        new_end = new_start + timedelta(hours=1)

        conflicts = AvailabilityService.check_booking_conflicts(
            db,
            test_tutor_profile.id,
            new_start,
            new_end,
            buffer_minutes=5
        )

        # Then
        assert len(conflicts) == 0


# Additional test scenarios to implement:
# - Recurring availability with exceptions (specific dates)
# - Batch availability import (e.g., Google Calendar sync)
# - Availability templates (copy from one tutor to another)
# - Peak hours pricing adjustments
# - Minimum advance booking time (e.g., 24h notice)
# - Maximum advance booking time (e.g., 3 months)
# - Last-minute availability (within 24h)
# - Automatic availability suggestions based on demand
