"""
Consolidated pytest configuration and shared fixtures.

This file consolidates test infrastructure from backend/tests/conftest.py
and tests/conftest.py to eliminate duplication and provide a single source
of test configuration.
"""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# =============================================================================
# Path Setup - Ensure backend is importable from repo root
# =============================================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# =============================================================================
# Test Environment Configuration
# =============================================================================

# Minimal, deterministic settings for tests
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-characters-long-123")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # Speed up hashing in tests

# =============================================================================
# Imports (after path setup)
# =============================================================================

import database  # noqa: E402
import models  # noqa: E402
from auth import get_password_hash  # noqa: E402
from core.security import TokenManager  # noqa: E402
from database import get_db  # noqa: E402
from main import app  # noqa: E402
from models import StudentProfile, TutorProfile, User  # noqa: E402
from models.base import Base  # noqa: E402

# =============================================================================
# Database Setup
# =============================================================================

# SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

TEST_ENGINE = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign keys for SQLite (important for referential integrity)
@event.listens_for(TEST_ENGINE, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints in SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

# Align global database state with test engine
database.engine = TEST_ENGINE
database.SessionLocal = TestingSessionLocal
database.Base = Base


def override_get_db() -> Generator[Session, None, None]:
    """Yield a database session backed by the test engine."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency globally
app.dependency_overrides[get_db] = override_get_db

# =============================================================================
# Core Fixtures
# =============================================================================


@pytest.fixture(autouse=True, scope="function")
def setup_database() -> Generator[None, None, None]:
    """Create fresh schema for every test function."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create database session for tests.

    Alias: db() also available for compatibility.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db(db_session: Session) -> Session:
    """Alias for db_session (for backward compatibility)."""
    return db_session


@pytest.fixture(scope="function")
def client(setup_database) -> Generator[TestClient, None, None]:
    """FastAPI test client with database setup."""
    with TestClient(app) as test_client:
        yield test_client


# =============================================================================
# User Creation Utilities
# =============================================================================


def _ensure_student_profile(db: Session, user: User) -> None:
    """Create a student profile for the user if missing."""
    if user.role == "student" and not db.query(StudentProfile).filter_by(user_id=user.id).first():
        db.add(StudentProfile(user_id=user.id))
        db.commit()


def create_test_user(
    db: Session,
    email: str,
    password: str,
    role: str,
    first_name: str = "Test",
    last_name: str = "User",
) -> User:
    """
    Unified function to create test users.

    Centralizes user creation logic to avoid duplication.
    """
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash(password),
        role=role,
        is_verified=True,
        is_active=True,
        first_name=first_name,
        last_name=last_name,
        currency="USD",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-create student profile if needed
    if role == "student":
        _ensure_student_profile(db, user)

    return user


def create_test_tutor_profile(
    db: Session,
    user_id: int,
    hourly_rate: float = 50.00,
) -> TutorProfile:
    """Create a minimal approved tutor profile for the given user."""
    profile = TutorProfile(
        user_id=user_id,
        title="Expert Test Tutor",
        headline="10 years experience",
        bio="Passionate about teaching.",
        hourly_rate=hourly_rate,
        experience_years=10,
        education="PhD in Education",
        languages=["English"],
        is_approved=True,
        profile_status="approved",
        timezone="UTC",
        currency="USD",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# =============================================================================
# User Fixtures
# =============================================================================


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create admin user for testing."""
    return create_test_user(
        db_session,
        email="admin@test.com",
        password="admin123",
        role="admin",
        first_name="Admin",
        last_name="User",
    )


@pytest.fixture
def tutor_user(db_session: Session) -> User:
    """Create tutor user with profile for testing."""
    user = create_test_user(
        db_session,
        email="tutor@test.com",
        password="tutor123",
        role="tutor",
        first_name="Test",
        last_name="Tutor",
    )

    # Create tutor profile
    profile = create_test_tutor_profile(db_session, user.id)
    user.tutor_profile = profile
    db_session.refresh(user)

    return user


@pytest.fixture
def student_user(db_session: Session) -> User:
    """Create student user for testing."""
    return create_test_user(
        db_session,
        email="student@test.com",
        password="student123",
        role="student",
        first_name="Test",
        last_name="Student",
    )


# =============================================================================
# Token Fixtures (Login-based)
# =============================================================================


@pytest.fixture
def admin_token(client: TestClient, admin_user: User) -> str:
    """Get admin auth token via login."""
    response = client.post(
        "/api/auth/login",
        data={"username": admin_user.email, "password": "admin123"}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def tutor_token(client: TestClient, tutor_user: User) -> str:
    """Get tutor auth token via login."""
    response = client.post(
        "/api/auth/login",
        data={"username": tutor_user.email, "password": "tutor123"}
    )
    assert response.status_code == 200, f"Tutor login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def student_token(client: TestClient, student_user: User) -> str:
    """Get student auth token via login."""
    response = client.post(
        "/api/auth/login",
        data={"username": student_user.email, "password": "student123"}
    )
    assert response.status_code == 200, f"Student login failed: {response.text}"
    return response.json()["access_token"]


# =============================================================================
# Token Fixtures (Direct - for unit tests without HTTP)
# =============================================================================


@pytest.fixture
def admin_token_direct(admin_user: User) -> str:
    """Get admin token directly (bypasses login endpoint)."""
    return TokenManager.create_access_token({"sub": admin_user.email})


@pytest.fixture
def tutor_token_direct(tutor_user: User) -> str:
    """Get tutor token directly (bypasses login endpoint)."""
    return TokenManager.create_access_token({"sub": tutor_user.email})


@pytest.fixture
def student_token_direct(student_user: User) -> str:
    """Get student token directly (bypasses login endpoint)."""
    return TokenManager.create_access_token({"sub": student_user.email})


# =============================================================================
# Additional Test Data Fixtures
# =============================================================================


@pytest.fixture
def test_subject(db_session: Session):
    """Create test subject."""
    from models import Subject

    subject = Subject(
        name="Mathematics",
        description="Math tutoring",
        category="STEM",
        is_active=True
    )
    db_session.add(subject)
    db_session.commit()
    db_session.refresh(subject)
    return subject


@pytest.fixture
def test_booking(db_session: Session, tutor_user: User, student_user: User, test_subject):
    """Create test booking."""
    from datetime import UTC, datetime, timedelta

    from models import Booking

    booking = Booking(
        tutor_profile_id=tutor_user.tutor_profile.id,
        student_id=student_user.id,
        subject_id=test_subject.id,
        start_time=datetime.now(UTC) + timedelta(days=1),
        end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
        topic="Calculus basics",
        hourly_rate=50.00,
        total_amount=50.00,
        currency="USD",
        status="PENDING",
        tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
        student_name=f"{student_user.first_name} {student_user.last_name}",
        subject_name=test_subject.name,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


# =============================================================================
# Legacy Compatibility Fixtures
# =============================================================================


@pytest.fixture
def test_student_token(db_session: Session) -> str:
    """
    JWT for the default student (legacy fixture).

    Creates student@example.com if it doesn't exist.
    """
    student = db_session.query(User).filter_by(email="student@example.com").first()
    if not student:
        student = create_test_user(
            db_session,
            email="student@example.com",
            password="password123",
            role="student",
        )
    return TokenManager.create_access_token({"sub": student.email})


@pytest.fixture
def test_tutor_token(db_session: Session) -> str:
    """
    JWT for a tutor user (legacy fixture).

    Creates tutor@example.com if it doesn't exist.
    """
    tutor = db_session.query(User).filter_by(email="tutor@example.com").first()
    if not tutor:
        tutor = create_test_user(
            db_session,
            email="tutor@example.com",
            password="password123",
            role="tutor",
        )
    return TokenManager.create_access_token({"sub": tutor.email})
