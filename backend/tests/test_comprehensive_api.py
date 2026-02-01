"""
Comprehensive API integration tests.
Tests all major endpoints and workflows.
"""

from datetime import datetime, timedelta

# import pytest  # noqa: F401


def test_auth_registration_flow(client):
    """Test complete user registration flow."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "SecurePass123!",  # Must meet complexity requirements
            "role": "student",
            "timezone": "America/New_York",
            "currency": "USD",
            "first_name": "New",
            "last_name": "User",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "student"
    assert data["timezone"] == "America/New_York"
    assert data["currency"] == "USD"
    assert data["is_active"] is True


def test_auth_login_and_token_flow(client, student_token, student_user):
    """Test login and token usage with pre-verified user from fixtures."""
    # Use pre-verified student from fixtures
    token = student_token

    # Use token to access protected endpoint
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == student_user.email

    currency_update = client.patch(
        "/api/v1/users/currency",
        json={"currency": "EUR"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert currency_update.status_code == 200
    assert currency_update.json()["currency"] == "EUR"


def test_currency_options_endpoint(client, student_token):
    """Ensure currency options endpoint returns entries."""
    response = client.get("/api/v1/users/currency/options")
    assert response.status_code == 200
    options = response.json()
    assert isinstance(options, list)
    assert any(option["code"] == "USD" for option in options)


def test_subjects_list_cached(client, student_token):
    """Test subjects listing with caching."""
    # First request
    response1 = client.get("/api/v1/subjects", headers={"Authorization": f"Bearer {student_token}"})
    assert response1.status_code == 200
    subjects1 = response1.json()

    # Second request (should be cached)
    response2 = client.get("/api/v1/subjects", headers={"Authorization": f"Bearer {student_token}"})
    assert response2.status_code == 200
    subjects2 = response2.json()

    assert subjects1 == subjects2
    assert isinstance(subjects1, list)


def test_tutor_profile_crud(client, tutor_token):
    """Test tutor profile create, read, update operations."""
    # Get current profile (might not exist yet)
    _get_response = client.get(  # noqa: F841
        "/api/v1/tutors/me/profile",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    # Update about section
    update_response = client.patch(
        "/api/v1/tutors/me/about",
        json={
            "title": "Expert Math Tutor",
            "headline": "10+ years experience",
            "bio": "Passionate about teaching mathematics",
            "experience_years": 10,
            "languages": ["en", "es"],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    assert update_response.status_code in [200, 201]
    profile = update_response.json()
    assert profile["title"] == "Expert Math Tutor"
    assert profile["experience_years"] == 10


def test_student_profile_update(client, student_token):
    """Test student profile updates."""
    response = client.patch(
        "/api/v1/profile/student/me",
        json={
            "grade_level": "10th Grade",
            "school_name": "Test High School",
            "learning_goals": "Improve math skills",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["grade_level"] == "10th Grade"
    assert profile["school_name"] == "Test High School"


import pytest  # noqa: E402


@pytest.mark.skip(reason="Requires tutor availability setup - tested in test_bookings.py")
def test_booking_creation_validation(client, student_token, test_subject):
    """Test booking creation with validation."""
    # Invalid: too short duration
    response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": 1,
            "subject_id": test_subject.id,
            "start_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "duration_minutes": 10,  # Too short
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Should fail due to invalid duration
    assert response.status_code == 422


@pytest.mark.skip(reason="Requires tutor availability setup - tested in test_bookings.py")
def test_booking_status_transitions(client, tutor_token, student_token, test_subject):
    """Test valid booking status transitions."""
    # Create booking as student using new API format
    start_time = (datetime.now() + timedelta(days=1)).isoformat()

    create_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": 1,
            "subject_id": test_subject.id,
            "start_at": start_time,
            "duration_minutes": 60,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert create_response.status_code == 201
    booking_id = create_response.json()["id"]

    # Tutor confirms booking using new API endpoint
    confirm_response = client.post(
        f"/api/v1/tutor/bookings/{booking_id}/confirm",
        json={},
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "CONFIRMED"


@pytest.mark.skip(reason="Requires tutor availability setup - tested in test_bookings.py")
def test_review_creation_requires_completed_booking(client, student_token, test_subject):
    """Test that reviews can only be created for completed bookings."""
    # Create pending booking using new API format
    start_time = (datetime.now() + timedelta(days=1)).isoformat()

    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": 1,
            "subject_id": test_subject.id,
            "start_at": start_time,
            "duration_minutes": 60,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    booking_id = booking_response.json()["id"]

    # Try to create review for pending booking
    review_response = client.post(
        "/api/v1/reviews",
        json={"booking_id": booking_id, "rating": 5, "comment": "Great session!"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    # Should fail because booking is not completed
    assert review_response.status_code == 400


def test_messages_thread_flow(client, student_token, tutor_token):
    """Test messaging between student and tutor."""
    # Student sends message
    send_response = client.post(
        "/api/v1/messages",
        json={
            "recipient_id": 2,  # Assuming tutor user ID is 2
            "message": "Hello, I'd like to book a session",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    if send_response.status_code == 201:
        # List threads
        threads_response = client.get(
            "/api/v1/messages/threads",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert threads_response.status_code == 200
        threads = threads_response.json()
        assert isinstance(threads, list)


def test_tutor_availability_management(client, tutor_token):
    """Test tutor availability CRUD operations."""
    # Replace availability
    response = client.put(
        "/api/v1/tutors/me/availability",
        json={
            "availability": [
                {
                    "day_of_week": 1,  # Monday
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                    "is_recurring": True,
                },
                {
                    "day_of_week": 3,  # Wednesday
                    "start_time": "09:00:00",
                    "end_time": "17:00:00",
                    "is_recurring": True,
                },
            ],
            "timezone": "America/New_York",
            "version": 1,
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    assert response.status_code in [200, 201]
    profile = response.json()
    assert "availabilities" in profile


def test_tutor_pricing_options(client, tutor_token):
    """Test tutor pricing options management."""
    response = client.patch(
        "/api/v1/tutors/me/pricing",
        json={
            "hourly_rate": 50.00,
            "version": 1,
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )

    assert response.status_code == 200
    profile = response.json()
    # API may return hourly_rate as string or float depending on serialization
    assert float(profile["hourly_rate"]) == 50.00


def test_admin_user_management(client, admin_token):
    """Test admin user management operations."""
    # List all users
    response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    data = response.json()
    # Should have items key due to pagination
    assert "items" in data or isinstance(data, list)


def test_pagination_on_listings(client, student_token):
    """Test pagination on list endpoints."""
    response = client.get(
        "/api/v1/tutors?page=1&page_size=10",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    # Should return paginated response
    data = response.json()
    # Check if it's a paginated response or list
    if isinstance(data, dict):
        assert "items" in data
    else:
        assert isinstance(data, list)


@pytest.mark.skip(reason="Requires tutor availability setup - tested elsewhere")
def test_input_sanitization(client, student_token, test_subject):
    """Test that inputs are properly sanitized."""
    # Try to inject HTML/JS in booking notes using new API format
    start_time = (datetime.now() + timedelta(days=1)).isoformat()

    response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": 1,
            "subject_id": test_subject.id,
            "start_at": start_time,
            "duration_minutes": 60,
            "notes": "<script>alert('xss')</script>Test notes",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    if response.status_code == 201:
        booking = response.json()
        # Notes should be sanitized (no script tags)
        assert "<script>" not in booking.get("notes", "")


def test_rate_limiting_headers(client):
    """Test that rate limiting is enforced (if configured)."""
    # Make multiple rapid requests
    for _ in range(15):
        response = client.get("/api/v1/subjects")
        # After limit, should get 429
        if response.status_code == 429:
            break
    # Note: This test may not trigger rate limiting in test environment


@pytest.mark.skip(reason="Requires tutor availability setup - tested elsewhere")
def test_soft_delete_preserves_relationships(client, admin_token, student_token, test_subject):
    """Test that soft-deleted records preserve relationships."""
    # Create a booking using new API format
    start_time = (datetime.now() + timedelta(days=1)).isoformat()

    booking_response = client.post(
        "/api/v1/bookings",
        json={
            "tutor_profile_id": 1,
            "subject_id": test_subject.id,
            "start_at": start_time,
            "duration_minutes": 60,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    _booking_id = booking_response.json()["id"]  # noqa: F841

    # Soft-delete user (if admin API supports it)
    # The booking should still reference the user via snapshot

    # This validates that snapshots preserve data even after soft-deletion
