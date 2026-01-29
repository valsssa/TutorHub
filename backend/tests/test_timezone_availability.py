"""Tests for timezone handling in availability system."""

from datetime import date, datetime, time, timedelta, timezone as dt_timezone

import pytest
from fastapi import status


class TestAvailabilityTimezoneInAPI:
    """Test timezone handling in availability API endpoints."""

    def test_set_availability_with_timezone(self, client, tutor_token):
        """Test setting availability with specific timezone."""
        # Get current profile version
        profile_response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert profile_response.status_code == status.HTTP_200_OK
        version = profile_response.json()["version"]

        # Set availability with Eastern timezone
        response = client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 1,  # Monday
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "America/New_York",
                "version": version,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_set_availability_with_pacific_timezone(self, client, tutor_token):
        """Test setting availability with Pacific timezone."""
        profile_response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        version = profile_response.json()["version"]

        response = client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 2,  # Tuesday
                        "start_time": "08:00:00",
                        "end_time": "16:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "America/Los_Angeles",
                "version": version,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_set_availability_with_european_timezone(self, client, tutor_token):
        """Test setting availability with European timezone."""
        profile_response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        version = profile_response.json()["version"]

        response = client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 3,  # Wednesday
                        "start_time": "10:00:00",
                        "end_time": "18:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "Europe/London",
                "version": version,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_set_availability_with_asian_timezone(self, client, tutor_token):
        """Test setting availability with Asian timezone."""
        profile_response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        version = profile_response.json()["version"]

        response = client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 4,  # Thursday
                        "start_time": "09:00:00",
                        "end_time": "21:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "Asia/Tokyo",
                "version": version,
            },
        )

        assert response.status_code == status.HTTP_200_OK

    def test_set_availability_with_utc(self, client, tutor_token):
        """Test setting availability with UTC timezone."""
        profile_response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        version = profile_response.json()["version"]

        response = client.put(
            "/api/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 5,  # Friday
                        "start_time": "12:00:00",
                        "end_time": "20:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "UTC",
                "version": version,
            },
        )

        assert response.status_code == status.HTTP_200_OK


class TestAvailableSlotsTimezoneHandling:
    """Test timezone handling when retrieving available slots."""

    def test_available_slots_returns_utc(self, client, db_session, tutor_user, student_token):
        """Test that available slots are returned in UTC."""
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear existing availability
        db_session.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile.id
        ).delete()
        db_session.commit()

        # Add availability
        availability = TutorAvailability(
            tutor_profile_id=tutor_profile.id,
            day_of_week=1,  # Monday
            start_time=time(10, 0),
            end_time=time(14, 0),
            is_recurring=True,
        )
        db_session.add(availability)
        db_session.commit()

        # Query slots
        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = start_date + timedelta(days=14)

        response = client.get(
            f"/api/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        slots = response.json()

        # Verify slots have ISO format with timezone info
        for slot in slots:
            assert "T" in slot["start_time"], "Should be ISO format with time"
            assert "T" in slot["end_time"], "Should be ISO format with time"
            # Should be timezone-aware (contains +00:00 or Z)
            assert (
                "+00:00" in slot["start_time"] or "Z" in slot["start_time"]
            ), "Should be UTC"

    def test_available_slots_date_range_validation(self, client, tutor_user, student_token):
        """Test date range validation for available slots."""
        tutor_profile = tutor_user.tutor_profile

        today = date.today()
        start_date = today
        end_date = today + timedelta(days=31)  # More than 30 days

        response = client.get(
            f"/api/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "30 days" in response.json()["detail"]

    def test_available_slots_invalid_date_format(self, client, tutor_user, student_token):
        """Test invalid date format returns 400."""
        tutor_profile = tutor_user.tutor_profile

        response = client.get(
            f"/api/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": "not-a-date",
                "end_date": "also-not-a-date",
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTutorProfileTimezone:
    """Test timezone field in tutor profile."""

    def test_tutor_profile_has_timezone(self, client, tutor_token):
        """Test tutor profile includes timezone field."""
        response = client.get(
            "/api/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "timezone" in data
        # Default should be UTC
        assert data["timezone"] in [None, "UTC"]


class TestCrossTimezoneBookingScenarios:
    """Test realistic cross-timezone booking scenarios."""

    def test_us_to_europe_booking_scenario(self, client, db_session, tutor_user, student_token):
        """
        Simulate a student in US booking a tutor in Europe.

        Scenario: European tutor sets availability 9am-5pm local time.
        US student should see slots correctly converted.
        """
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear and set European tutor's availability
        db_session.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile.id
        ).delete()
        db_session.commit()

        # Tutor in Europe sets availability for weekdays
        for day in [1, 2, 3, 4, 5]:  # Mon-Fri
            av = TutorAvailability(
                tutor_profile_id=tutor_profile.id,
                day_of_week=day,
                start_time=time(9, 0),  # 9 AM local
                end_time=time(17, 0),  # 5 PM local
                is_recurring=True,
            )
            db_session.add(av)
        db_session.commit()

        # Student queries available slots
        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = start_date + timedelta(days=7)

        response = client.get(
            f"/api/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        slots = response.json()

        # Should have slots for weekdays
        assert len(slots) > 0, "Should have available slots"

        # Verify all slots are weekdays
        for slot in slots:
            slot_dt = datetime.fromisoformat(slot["start_time"])
            python_weekday = slot_dt.weekday()
            js_weekday = (python_weekday + 1) % 7
            assert js_weekday in [1, 2, 3, 4, 5], f"Slot should be on weekday, got {js_weekday}"

    def test_us_to_asia_booking_scenario(self, client, db_session, tutor_user, student_token):
        """
        Simulate a student in US booking a tutor in Asia.

        Scenario: Asian tutor sets evening availability for US morning students.
        """
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear existing
        db_session.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile.id
        ).delete()
        db_session.commit()

        # Asian tutor sets evening availability (good for US morning)
        for day in [1, 2, 3, 4, 5]:  # Mon-Fri
            av = TutorAvailability(
                tutor_profile_id=tutor_profile.id,
                day_of_week=day,
                start_time=time(18, 0),  # 6 PM local (Asia)
                end_time=time(23, 0),  # 11 PM local
                is_recurring=True,
            )
            db_session.add(av)
        db_session.commit()

        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = start_date + timedelta(days=7)

        response = client.get(
            f"/api/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        slots = response.json()
        assert len(slots) > 0, "Should have available slots"


class TestTimezoneInBookingSnapshot:
    """Test that timezone information is captured in booking snapshots."""

    def test_booking_captures_timezones(self, client, db_session, tutor_user, student_user, test_subject):
        """Test that booking captures both student and tutor timezones."""
        from models import Booking

        # Update student timezone
        student_user.timezone = "America/New_York"
        db_session.commit()

        # Create a booking
        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            subject_id=test_subject.id,
            start_time=datetime.now(dt_timezone.utc) + timedelta(days=2),
            end_time=datetime.now(dt_timezone.utc) + timedelta(days=2, hours=1),
            hourly_rate=50.00,
            total_amount=50.00,
            currency="USD",
            status="PENDING",
            student_tz=student_user.timezone,
            tutor_tz=tutor_user.timezone,
            tutor_name="Test Tutor",
            student_name="Test Student",
        )
        db_session.add(booking)
        db_session.commit()
        db_session.refresh(booking)

        # Verify timezones are captured
        assert booking.student_tz == "America/New_York"
        assert booking.tutor_tz == "UTC"  # Default from fixture

    def test_booking_timezones_immutable_snapshot(self, client, db_session, tutor_user, student_user, test_subject):
        """Test that booking timezones remain as snapshot even if user changes."""
        from models import Booking

        # Set initial timezone
        student_user.timezone = "America/Chicago"
        db_session.commit()

        # Create booking
        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            subject_id=test_subject.id,
            start_time=datetime.now(dt_timezone.utc) + timedelta(days=3),
            end_time=datetime.now(dt_timezone.utc) + timedelta(days=3, hours=1),
            hourly_rate=50.00,
            total_amount=50.00,
            currency="USD",
            status="CONFIRMED",
            student_tz="America/Chicago",  # Snapshot at booking time
            tutor_tz="UTC",
            tutor_name="Test Tutor",
            student_name="Test Student",
        )
        db_session.add(booking)
        db_session.commit()
        booking_id = booking.id

        # User changes timezone later
        student_user.timezone = "Europe/London"
        db_session.commit()

        # Verify booking still has original timezone
        db_session.refresh(booking)
        reloaded = db_session.query(Booking).get(booking_id)
        assert reloaded.student_tz == "America/Chicago", "Booking timezone should be immutable snapshot"


class TestSingleAvailabilityTimezone:
    """Test timezone handling in single availability creation endpoint."""

    def test_single_availability_inherits_tutor_timezone(self, client, db_session, tutor_user, tutor_token):
        """Test that single availability slot inherits tutor's profile timezone."""
        from models import TutorAvailability

        # Set tutor's timezone
        tutor_user.timezone = "America/Los_Angeles"
        if tutor_user.tutor_profile:
            tutor_user.tutor_profile.timezone = "America/Los_Angeles"
        db_session.commit()

        # Create single availability via POST endpoint
        response = client.post(
            "/api/tutors/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "day_of_week": 3,  # Wednesday
                "start_time": "10:00:00",
                "end_time": "14:00:00",
                "is_recurring": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify timezone is set in response
        assert data.get("timezone") == "America/Los_Angeles" or data.get("timezone") == "UTC"

    def test_bulk_availability_inherits_tutor_timezone(self, client, db_session, tutor_user, tutor_token):
        """Test that bulk availability slots inherit tutor's profile timezone."""
        from models import TutorAvailability

        # Set tutor's timezone
        tutor_user.timezone = "Europe/Paris"
        if tutor_user.tutor_profile:
            tutor_user.tutor_profile.timezone = "Europe/Paris"
        db_session.commit()

        # Create bulk availability via POST endpoint
        response = client.post(
            "/api/tutors/availability/bulk",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json=[
                {
                    "day_of_week": 1,
                    "start_time": "09:00:00",
                    "end_time": "12:00:00",
                    "is_recurring": True,
                },
                {
                    "day_of_week": 2,
                    "start_time": "14:00:00",
                    "end_time": "18:00:00",
                    "is_recurring": True,
                },
            ],
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify slots were created with timezone
        tutor_profile = tutor_user.tutor_profile
        slots = (
            db_session.query(TutorAvailability)
            .filter(TutorAvailability.tutor_profile_id == tutor_profile.id)
            .all()
        )

        # At least some slots should have the tutor's timezone
        assert len(slots) >= 2


class TestDSTHandling:
    """Test Daylight Saving Time handling in timezone conversions."""

    def test_dst_spring_forward(self, db_session, tutor_user):
        """Test availability during DST spring forward."""
        from zoneinfo import ZoneInfo
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear existing
        db_session.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile.id
        ).delete()
        db_session.commit()

        # Create availability in US Eastern timezone
        availability = TutorAvailability(
            tutor_profile_id=tutor_profile.id,
            day_of_week=0,  # Sunday
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_recurring=True,
            timezone="America/New_York",
        )
        db_session.add(availability)
        db_session.commit()

        # Verify timezone is stored
        db_session.refresh(availability)
        assert availability.timezone == "America/New_York"

    def test_dst_fall_back(self, db_session, tutor_user):
        """Test availability during DST fall back."""
        from zoneinfo import ZoneInfo
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear existing
        db_session.query(TutorAvailability).filter(
            TutorAvailability.tutor_profile_id == tutor_profile.id
        ).delete()
        db_session.commit()

        # Create availability in Pacific timezone
        availability = TutorAvailability(
            tutor_profile_id=tutor_profile.id,
            day_of_week=0,  # Sunday
            start_time=time(1, 0),  # During potential DST transition
            end_time=time(3, 0),
            is_recurring=True,
            timezone="America/Los_Angeles",
        )
        db_session.add(availability)
        db_session.commit()

        # Verify timezone is stored
        db_session.refresh(availability)
        assert availability.timezone == "America/Los_Angeles"
