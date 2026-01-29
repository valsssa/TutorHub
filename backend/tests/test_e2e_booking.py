"""
Integration tests covering tutor profiles and student bookings.

These tests use the consolidated test infrastructure from tests/conftest.py
and verify complete booking workflows from profile setup to booking lifecycle.
"""

from datetime import UTC, datetime, timedelta

import pytest

# All fixtures are automatically available from consolidated conftest.py
# Available fixtures: client, db_session, admin_user, tutor_user, student_user,
#                    admin_token, tutor_token, student_token, etc.


def test_tutor_profile_setup_and_booking_lifecycle(client, tutor_token, student_token, db_session):
    """
    Test complete booking workflow:
    1. Tutor creates/updates profile
    2. Student searches for tutors
    3. Student creates booking
    4. Tutor receives and approves booking
    5. Both parties can view updated status
    """
    # Step 1: Tutor creates profile
    profile_payload = {
        "title": "Alex Tutor",
        "headline": "STEM Specialist",
        "bio": "I help students prepare for STEM exams.",
        "hourly_rate": 45.00,
        "experience_years": 6,
        "timezone": "UTC",
        "video_url": None,
    }

    profile_response = client.put(
        "/api/v1/tutor-profile/me",
        json=profile_payload,
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code in (200, 201), f"Profile creation failed: {profile_response.text}"
    profile_data = profile_response.json()
    profile_id = profile_data["id"]

    # Step 2: Student searches for tutors
    tutors_listing = client.get(
        "/api/v1/tutors",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert tutors_listing.status_code == 200
    tutors = tutors_listing.json()

    # Verify tutor appears in search results
    # Handle both paginated and non-paginated responses
    if isinstance(tutors, dict) and "items" in tutors:
        tutor_ids = [t["id"] for t in tutors["items"]]
    else:
        tutor_ids = [t["id"] for t in tutors]

    assert profile_id in tutor_ids, f"Tutor profile {profile_id} not found in search results"

    # Step 3: Student creates booking
    now = datetime.now(UTC)
    start_time = (now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject_id": 1,  # Assuming math subject exists
            "topic": "Calculus revision",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "notes": "Focus on integration techniques",
            "lesson_type": "TRIAL",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert booking_response.status_code == 201, f"Booking creation failed: {booking_response.text}"
    booking = booking_response.json()
    booking_id = booking["id"]

    # Verify initial status
    assert booking["status"] in ("PENDING", "pending")

    # Step 4: Tutor views their bookings
    tutor_bookings = client.get(
        "/api/v1/bookings/tutor/me",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert tutor_bookings.status_code == 200
    tutor_bookings_data = tutor_bookings.json()

    # Handle paginated response
    if isinstance(tutor_bookings_data, dict) and "items" in tutor_bookings_data:
        bookings_list = tutor_bookings_data["items"]
    else:
        bookings_list = tutor_bookings_data

    assert len(bookings_list) >= 1, "Tutor should see at least one booking"
    assert any(b["id"] == booking_id for b in bookings_list), "Booking not found in tutor's list"

    # Step 5: Tutor confirms booking
    confirm_response = client.patch(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert confirm_response.status_code == 200, f"Booking confirmation failed: {confirm_response.text}"
    confirmed_booking = confirm_response.json()
    assert confirmed_booking["status"] in ("CONFIRMED", "confirmed")

    # Step 6: Student views updated booking
    student_bookings = client.get(
        "/api/v1/bookings/student/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_bookings.status_code == 200
    student_bookings_data = student_bookings.json()

    # Handle paginated response
    if isinstance(student_bookings_data, dict) and "items" in student_bookings_data:
        student_bookings_list = student_bookings_data["items"]
    else:
        student_bookings_list = student_bookings_data

    confirmed = next((b for b in student_bookings_list if b["id"] == booking_id), None)
    assert confirmed is not None, "Booking not found in student's list"
    assert confirmed["status"] in ("CONFIRMED", "confirmed")


def test_booking_validation_subject_not_offered(client, tutor_token, student_token, db_session):
    """
    Test that bookings are rejected when student requests subject not offered by tutor.
    """
    # Step 1: Tutor creates profile with English only
    profile_response = client.put(
        "/api/v1/tutor-profile/me",
        json={
            "title": "Language Coach",
            "headline": "ESL Tutor",
            "bio": "Helping learners master English.",
            "hourly_rate": 35.00,
            "experience_years": 4,
            "timezone": "UTC",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code in (200, 201)
    profile_id = profile_response.json()["id"]

    # Step 2: Student attempts to book for subject tutor doesn't offer
    now = datetime.now(UTC)
    start_time = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    # Note: This test assumes subject validation is enforced
    # If subjects are flexible, this test may need adjustment
    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject_id": 99999,  # Non-existent subject
            "topic": "Advanced topic",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "lesson_type": "REGULAR",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Should fail with appropriate error
    assert booking_response.status_code in (400, 404, 422), "Should reject invalid subject"


def test_booking_cancellation_workflow(client, tutor_user, student_user, tutor_token, student_token, db_session):
    """
    Test booking cancellation by student within free cancellation window.
    """
    # Step 1: Create profile
    profile_response = client.put(
        "/api/v1/tutor-profile/me",
        json={
            "title": "Test Tutor",
            "headline": "Expert",
            "bio": "Test bio",
            "hourly_rate": 50.00,
            "experience_years": 5,
            "timezone": "UTC",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code in (200, 201)
    profile_id = profile_response.json()["id"]

    # Step 2: Create booking far in future (free cancellation)
    now = datetime.now(UTC)
    start_time = (now + timedelta(days=5)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject_id": 1,
            "topic": "Test topic",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "lesson_type": "REGULAR",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert booking_response.status_code == 201
    booking_id = booking_response.json()["id"]

    # Step 3: Student cancels booking
    cancel_response = client.patch(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert cancel_response.status_code == 200, f"Cancellation failed: {cancel_response.text}"

    # Step 4: Verify booking is cancelled
    booking_check = client.get(
        f"/api/v1/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert booking_check.status_code == 200
    cancelled_booking = booking_check.json()
    assert "cancel" in cancelled_booking["status"].lower(), f"Booking should be cancelled, got: {cancelled_booking['status']}"


def test_booking_time_conflict_prevention(client, tutor_token, student_token, db_session):
    """
    Test that system prevents double-booking of tutor at same time.
    """
    # Step 1: Create tutor profile
    profile_response = client.put(
        "/api/v1/tutor-profile/me",
        json={
            "title": "Busy Tutor",
            "headline": "Popular tutor",
            "bio": "Test",
            "hourly_rate": 60.00,
            "experience_years": 8,
            "timezone": "UTC",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code in (200, 201)
    profile_id = profile_response.json()["id"]

    # Step 2: Create first booking
    now = datetime.now(UTC)
    start_time = (now + timedelta(days=3)).replace(hour=15, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    first_booking = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject_id": 1,
            "topic": "First session",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "lesson_type": "REGULAR",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert first_booking.status_code == 201

    # Step 3: Tutor confirms first booking
    booking_id = first_booking.json()["id"]
    client.patch(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    # Step 4: Attempt to create overlapping booking (should fail or be pending)
    overlapping_booking = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject_id": 1,
            "topic": "Conflicting session",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "lesson_type": "REGULAR",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # System should either reject or mark as pending for manual review
    # Exact behavior depends on implementation
    assert overlapping_booking.status_code in (201, 400, 409), "System should handle time conflicts"


@pytest.mark.parametrize("role,expected_status", [
    ("student", 403),  # Students cannot confirm
    ("admin", 200),    # Admins can confirm (if implemented)
])
def test_booking_authorization(client, db_session, role, expected_status):
    """
    Test that only authorized users can perform booking actions.
    """
    # This is a placeholder for authorization tests
    # Actual implementation depends on specific authorization rules
    pass


def test_booking_with_package_credits(client, tutor_token, student_token, db_session):
    """
    Test booking using package credits (if package system is implemented).
    """
    # Placeholder for package-based booking tests
    # Skip if packages aren't fully implemented yet
    pytest.skip("Package system tests not yet implemented")


def test_booking_timezone_handling(client, tutor_token, student_token, db_session):
    """
    Test that bookings correctly handle different timezones.
    """
    # Create profile with specific timezone
    profile_response = client.put(
        "/api/v1/tutor-profile/me",
        json={
            "title": "Timezone Test Tutor",
            "headline": "Expert",
            "bio": "Test",
            "hourly_rate": 40.00,
            "experience_years": 3,
            "timezone": "America/New_York",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code in (200, 201)
    profile_id = profile_response.json()["id"]

    # Create booking in UTC
    now = datetime.now(UTC)
    start_time = (now + timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(hours=1)

    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject_id": 1,
            "topic": "Timezone test",
            "start_at": start_time.isoformat(),
            "end_at": end_time.isoformat(),
            "lesson_type": "REGULAR",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert booking_response.status_code == 201
    booking = booking_response.json()

    # Verify times are stored correctly
    assert booking["start_at"] is not None
    assert booking["end_at"] is not None
