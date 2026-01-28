"""Integration tests covering tutor profiles and student bookings."""

import datetime
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend modules are importable when tests run from repo root
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from auth import get_password_hash  # noqa: E402
from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from models import User  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@test-db:5432/authapp_test")

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _create_user(email: str, role: str, password: str = "password123") -> None:
    db = TestingSessionLocal()
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.close()


def _login(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post(
        "/token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.json()
    return response.json()["access_token"]


@pytest.fixture
def api_client():
    return TestClient(app)


def test_tutor_profile_setup_and_booking_lifecycle(api_client):
    tutor_email = "booking-tutor@test.com"
    student_email = "booking-student@test.com"
    _create_user(tutor_email, "tutor")
    _create_user(student_email, "student")

    tutor_token = _login(api_client, tutor_email)
    student_token = _login(api_client, student_email)

    profile_payload = {
        "display_name": "Alex Tutor",
        "headline": "STEM Specialist",
        "bio": "I help students prepare for STEM exams.",
        "hourly_rate": "45.00",
        "experience_years": 6,
        "timezone": "UTC",
        "video_url": None,
        "subjects": [
            {
                "name": "Mathematics",
                "proficiency_level": "advanced",
                "years_experience": 6,
            },
            {"name": "Physics", "proficiency_level": "expert"},
        ],
    }

    profile_response = api_client.put(
        "/tutors/me/profile",
        json=profile_payload,
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code == 200, profile_response.json()
    profile_id = profile_response.json()["id"]

    tutors_listing = api_client.get(
        "/tutors",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert tutors_listing.status_code == 200
    assert any(tutor["id"] == profile_id for tutor in tutors_listing.json())

    now = datetime.datetime.now(datetime.UTC)
    start_time = (now + datetime.timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(hours=1)

    booking_response = api_client.post(
        "/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject": "Mathematics",
            "topic": "Calculus revision",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "notes": "Focus on integration techniques",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert booking_response.status_code == 201, booking_response.json()
    booking_id = booking_response.json()["id"]

    tutor_bookings = api_client.get(
        "/bookings/me",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert tutor_bookings.status_code == 200
    assert len(tutor_bookings.json()) == 1

    approve_response = api_client.patch(
        f"/bookings/{booking_id}",
        json={
            "status": "approved",
            "join_url": "https://example.com/session-link",
            "notes": "Looking forward to it!",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert approve_response.status_code == 200, approve_response.json()
    assert approve_response.json()["status"] == "approved"

    student_bookings = api_client.get(
        "/bookings/me",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert student_bookings.status_code == 200
    assert student_bookings.json()[0]["status"] == "approved"


def test_booking_rejects_unsupported_subject(api_client):
    tutor_email = "subject-tutor@test.com"
    student_email = "subject-student@test.com"
    _create_user(tutor_email, "tutor")
    _create_user(student_email, "student")

    tutor_token = _login(api_client, tutor_email)
    student_token = _login(api_client, student_email)

    profile_response = api_client.put(
        "/tutors/me/profile",
        json={
            "display_name": "Language Coach",
            "headline": "ESL Tutor",
            "bio": "Helping learners master English.",
            "hourly_rate": "35.00",
            "experience_years": 4,
            "timezone": "UTC",
            "video_url": None,
            "subjects": [{"name": "English", "proficiency_level": "advanced"}],
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert profile_response.status_code == 200
    profile_id = profile_response.json()["id"]

    now = datetime.datetime.now(datetime.UTC)
    start_time = (now + datetime.timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = start_time + datetime.timedelta(hours=1)

    response = api_client.post(
        "/bookings",
        json={
            "tutor_profile_id": profile_id,
            "subject": "Spanish",
            "topic": "Conversational practice",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 400
    assert "not offered" in response.json()["detail"]
