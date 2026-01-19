"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from auth import get_password_hash
from database import Base, get_db
from main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def admin_user(db_session):
    """Create admin user for testing."""
    from models import User

    user = User(
        email="admin@test.com".lower(),
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_verified=True,
        is_active=True,
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def tutor_user(db_session):
    """Create tutor user with profile for testing."""
    from models import TutorProfile, User

    user = User(
        email="tutor@test.com".lower(),
        hashed_password=get_password_hash("tutor123"),
        role="tutor",
        is_verified=True,
        is_active=True,
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.flush()

    # Create tutor profile
    profile = TutorProfile(
        user_id=user.id,
        title="Expert Math Tutor",
        headline="10 years experience",
        bio="Passionate about mathematics education.",
        hourly_rate=50.00,
        experience_years=10,
        education="PhD in Mathematics",
        languages=["English"],
        is_approved=True,
        profile_status="approved",
        currency="USD",
        timezone="UTC",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(profile)

    user.tutor_profile = profile
    return user


@pytest.fixture
def student_user(db_session):
    """Create student user for testing."""
    from models import User

    user = User(
        email="student@test.com".lower(),
        hashed_password=get_password_hash("student123"),
        role="student",
        is_verified=True,
        is_active=True,
        currency="USD",
        timezone="UTC",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin auth token."""
    response = client.post(
        "/api/auth/login", data={"username": admin_user.email, "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def tutor_token(client, tutor_user):
    """Get tutor auth token."""
    response = client.post(
        "/api/auth/login", data={"username": tutor_user.email, "password": "tutor123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def student_token(client, student_user):
    """Get student auth token."""
    response = client.post(
        "/api/auth/login",
        data={"username": student_user.email, "password": "student123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def test_subject(db_session):
    """Create test subject."""
    from models import Subject

    subject = Subject(
        name="Mathematics", description="Math tutoring", category="STEM", is_active=True
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def test_booking(db_session, tutor_user, student_user, test_subject):
    """Create test booking."""
    from datetime import datetime, timedelta

    from models import Booking

    booking = Booking(
        tutor_profile_id=tutor_user.tutor_profile.id,
        student_id=student_user.id,
        subject_id=test_subject.id,
        start_time=datetime.utcnow() + timedelta(days=1),
        end_time=datetime.utcnow() + timedelta(days=1, hours=1),
        topic="Calculus basics",
        hourly_rate=50.00,
        total_amount=50.00,
        status="pending",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking
