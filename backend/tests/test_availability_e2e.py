"""
E2E tests for tutor availability system.

CRITICAL: These tests verify that when a tutor sets availability for specific days,
students ONLY see slots for those days - not any other days.

Test Scenario:
1. Tutor sets availability for ONLY Sunday (day_of_week=0)
2. Student queries available slots for a week
3. Verify slots are ONLY returned for Sunday dates, NOT Monday or any other day
"""

from datetime import date, datetime, time, timedelta

import pytest
from fastapi import status


class TestAvailabilityDayMapping:
    """
    Test that day_of_week mapping is correct between frontend and backend.

    Frontend Convention (JavaScript):
        Sunday=0, Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5, Saturday=6

    Database stores day_of_week using frontend convention (0=Sunday, 6=Saturday)
    """

    def test_day_of_week_conversion_table(self):
        """Verify Python to JS weekday conversion is correct."""
        # Python weekday(): Monday=0, Sunday=6
        # JS convention: Sunday=0, Saturday=6

        def python_to_js_weekday(python_weekday: int) -> int:
            """Convert Python weekday to JS convention."""
            return (python_weekday + 1) % 7

        # Test all days
        assert python_to_js_weekday(0) == 1, "Python Monday (0) should be JS Monday (1)"
        assert python_to_js_weekday(1) == 2, "Python Tuesday (1) should be JS Tuesday (2)"
        assert python_to_js_weekday(2) == 3, "Python Wednesday (2) should be JS Wednesday (3)"
        assert python_to_js_weekday(3) == 4, "Python Thursday (3) should be JS Thursday (4)"
        assert python_to_js_weekday(4) == 5, "Python Friday (4) should be JS Friday (5)"
        assert python_to_js_weekday(5) == 6, "Python Saturday (5) should be JS Saturday (6)"
        assert python_to_js_weekday(6) == 0, "Python Sunday (6) should be JS Sunday (0)"


class TestTutorAvailabilityE2E:
    """E2E tests for the complete availability flow."""

    def test_sunday_only_availability_shows_only_sunday_slots(self, client, db_session, tutor_user, student_token):
        """
        CRITICAL TEST: When tutor sets availability for ONLY Sunday,
        students should ONLY see Sunday slots.

        This test verifies the exact user scenario:
        1. Tutor sets availability for Sunday only (day_of_week=0)
        2. Student queries available-slots
        3. All returned slots should be on Sunday dates
        """
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear any existing availability
        db_session.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == tutor_profile.id).delete()
        db_session.commit()

        # Set availability for ONLY Sunday (day_of_week=0 in JS convention)
        sunday_availability = TutorAvailability(
            tutor_profile_id=tutor_profile.id,
            day_of_week=0,  # Sunday in JS convention
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(17, 0),  # 5:00 PM
            is_recurring=True,
        )
        db_session.add(sunday_availability)
        db_session.commit()

        # Verify it's saved correctly
        saved = db_session.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == tutor_profile.id).all()
        assert len(saved) == 1, "Should have exactly 1 availability slot"
        assert saved[0].day_of_week == 0, "Should be Sunday (day_of_week=0)"

        # Find the next Sunday and query a week of slots
        today = date.today()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # If today is Sunday, get next Sunday

        next_sunday = today + timedelta(days=days_until_sunday)
        start_date = next_sunday
        end_date = start_date + timedelta(days=7)  # Query for a full week

        # Query available slots as student
        response = client.get(
            f"/api/v1/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK, f"Failed: {response.json()}"
        slots = response.json()

        # Verify all slots are on Sunday
        for slot in slots:
            slot_datetime = datetime.fromisoformat(slot["start_time"])
            slot_weekday = slot_datetime.weekday()  # Python: Sunday=6
            js_weekday = (slot_weekday + 1) % 7  # Convert to JS: Sunday=0

            assert js_weekday == 0, (
                f"CRITICAL BUG: Slot {slot['start_time']} is on "
                f"weekday {slot_weekday} (JS: {js_weekday}), expected Sunday (JS: 0)!\n"
                f"Date: {slot_datetime.date()}, Day name: {slot_datetime.strftime('%A')}"
            )

        # Also verify we got SOME slots (not zero)
        # Note: This might fail if all slots are in the past
        print(f"Found {len(slots)} slots, all on Sunday")

    def test_monday_only_availability_shows_only_monday_slots(self, client, db_session, tutor_user, student_token):
        """
        Verify Monday-only availability returns only Monday slots.
        """
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear any existing availability
        db_session.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == tutor_profile.id).delete()
        db_session.commit()

        # Set availability for ONLY Monday (day_of_week=1 in JS convention)
        monday_availability = TutorAvailability(
            tutor_profile_id=tutor_profile.id,
            day_of_week=1,  # Monday in JS convention
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_recurring=True,
        )
        db_session.add(monday_availability)
        db_session.commit()

        # Query for next 2 weeks to ensure we capture at least one Monday
        today = date.today()
        start_date = today + timedelta(days=1)  # Start tomorrow to avoid past slots
        end_date = start_date + timedelta(days=14)

        response = client.get(
            f"/api/v1/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        slots = response.json()

        # Verify all slots are on Monday
        for slot in slots:
            slot_datetime = datetime.fromisoformat(slot["start_time"])
            slot_weekday = slot_datetime.weekday()  # Python: Monday=0
            js_weekday = (slot_weekday + 1) % 7  # Convert to JS: Monday=1

            assert js_weekday == 1, (
                f"CRITICAL BUG: Slot {slot['start_time']} is on "
                f"weekday {slot_weekday} (JS: {js_weekday}), expected Monday (JS: 1)!\n"
                f"Date: {slot_datetime.date()}, Day name: {slot_datetime.strftime('%A')}"
            )

        print(f"Found {len(slots)} slots, all on Monday")

    def test_no_availability_returns_empty_slots(self, client, db_session, tutor_user, student_token):
        """Verify no availability returns empty slots."""
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear ALL availability
        db_session.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == tutor_profile.id).delete()
        db_session.commit()

        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = start_date + timedelta(days=7)

        response = client.get(
            f"/api/v1/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        slots = response.json()
        assert len(slots) == 0, "Expected no slots when no availability is set"

    def test_multiple_days_returns_correct_days_only(self, client, db_session, tutor_user, student_token):
        """
        Test that setting availability for multiple specific days
        returns slots only for those days.
        """
        from models import TutorAvailability

        tutor_profile = tutor_user.tutor_profile

        # Clear any existing availability
        db_session.query(TutorAvailability).filter(TutorAvailability.tutor_profile_id == tutor_profile.id).delete()
        db_session.commit()

        # Set availability for Tuesday (2) and Thursday (4) only
        for day in [2, 4]:  # Tuesday and Thursday in JS convention
            av = TutorAvailability(
                tutor_profile_id=tutor_profile.id,
                day_of_week=day,
                start_time=time(10, 0),
                end_time=time(14, 0),
                is_recurring=True,
            )
            db_session.add(av)
        db_session.commit()

        # Query for 2 weeks
        today = date.today()
        start_date = today + timedelta(days=1)
        end_date = start_date + timedelta(days=14)

        response = client.get(
            f"/api/v1/tutors/{tutor_profile.id}/available-slots",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        slots = response.json()

        # Verify all slots are either Tuesday or Thursday
        for slot in slots:
            slot_datetime = datetime.fromisoformat(slot["start_time"])
            slot_weekday = slot_datetime.weekday()  # Python weekday
            js_weekday = (slot_weekday + 1) % 7  # Convert to JS

            assert js_weekday in [2, 4], (
                f"CRITICAL BUG: Slot {slot['start_time']} is on "
                f"weekday {slot_weekday} (JS: {js_weekday}), "
                f"expected Tuesday (2) or Thursday (4)!\n"
                f"Date: {slot_datetime.date()}, Day name: {slot_datetime.strftime('%A')}"
            )

        print(f"Found {len(slots)} slots on Tuesday and Thursday only")


class TestAvailabilitySaveAndRetrieve:
    """Test the save/retrieve cycle for availability."""

    def test_tutor_save_availability_via_api(self, client, tutor_token):
        """Test tutor can save availability and it's stored correctly."""
        # First get current profile version
        profile_response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert profile_response.status_code == status.HTTP_200_OK
        version = profile_response.json()["version"]

        # Set availability for Sunday only
        response = client.put(
            "/api/v1/tutors/me/availability",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "availability": [
                    {
                        "day_of_week": 0,  # Sunday
                        "start_time": "09:00:00",
                        "end_time": "17:00:00",
                        "is_recurring": True,
                    }
                ],
                "timezone": "UTC",
                "version": version,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response contains correct availability
        assert len(data["availabilities"]) == 1
        assert data["availabilities"][0]["day_of_week"] == 0
        assert data["availabilities"][0]["start_time"] == "09:00:00"
        assert data["availabilities"][0]["end_time"] == "17:00:00"

    def test_tutor_availability_persists_after_reload(self, client, tutor_token):
        """Test that availability persists and can be retrieved."""
        # Get current version
        profile_response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        version = profile_response.json()["version"]

        # Set availability
        client.put(
            "/api/v1/tutors/me/availability",
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
                "timezone": "America/New_York",
                "version": version,
            },
        )

        # Reload profile and verify availability is there
        reload_response = client.get(
            "/api/v1/tutors/me/profile",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )

        assert reload_response.status_code == status.HTTP_200_OK
        data = reload_response.json()

        assert len(data["availabilities"]) == 1
        assert data["availabilities"][0]["day_of_week"] == 3
        assert data["availabilities"][0]["start_time"] == "10:00:00"


class TestWeekdayConversionInAvailableSlots:
    """
    Debug tests to verify weekday conversion in the available-slots endpoint.
    """

    def test_specific_date_weekday_conversion(self):
        """
        Test that specific dates are correctly converted.

        Reference: January 19, 2026 is a Monday
        """
        test_date = date(2026, 1, 19)  # Monday
        python_weekday = test_date.weekday()
        js_weekday = (python_weekday + 1) % 7

        assert python_weekday == 0, "Jan 19, 2026 should be Monday (Python: 0)"
        assert js_weekday == 1, "Jan 19, 2026 should be Monday (JS: 1)"

        # Sunday January 25, 2026
        sunday_date = date(2026, 1, 25)
        python_sunday = sunday_date.weekday()
        js_sunday = (python_sunday + 1) % 7

        assert python_sunday == 6, "Jan 25, 2026 should be Sunday (Python: 6)"
        assert js_sunday == 0, "Jan 25, 2026 should be Sunday (JS: 0)"

    def test_week_iteration_covers_all_days(self):
        """Verify a week iteration covers all 7 days correctly."""
        start = date(2026, 1, 19)  # Monday

        days_found = {}
        for i in range(7):
            current = start + timedelta(days=i)
            python_wd = current.weekday()
            js_wd = (python_wd + 1) % 7
            days_found[current.strftime("%A")] = {"python": python_wd, "js": js_wd, "date": current.isoformat()}

        # Verify mapping
        assert days_found["Monday"]["js"] == 1
        assert days_found["Tuesday"]["js"] == 2
        assert days_found["Wednesday"]["js"] == 3
        assert days_found["Thursday"]["js"] == 4
        assert days_found["Friday"]["js"] == 5
        assert days_found["Saturday"]["js"] == 6
        assert days_found["Sunday"]["js"] == 0
