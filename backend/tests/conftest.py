"""
Backend pytest configuration and shared fixtures.

This file provides all fixtures needed for backend testing.
Uses PostgreSQL for accurate testing with PostgreSQL-specific types.
Uses transaction-based isolation for speed and consistency.
"""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# =============================================================================
# Path Setup - Ensure backend modules are importable
# =============================================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# =============================================================================
# Test Environment Configuration
# =============================================================================

# Use test database - this connects to the PostgreSQL container
# Falls back to local PostgreSQL if no environment variable is set
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/authapp_test"
    )
)

# Ensure we use a test database
if "test" not in TEST_DATABASE_URL.lower():
    # Replace database name with test database
    TEST_DATABASE_URL = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/authapp_test"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-characters-long-123")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # Speed up hashing in tests
os.environ["SKIP_STARTUP_MIGRATIONS"] = "true"  # Skip migrations during tests

# =============================================================================
# Imports (after path setup and env config)
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

TEST_ENGINE = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

# Align global database state with test engine
database.engine = TEST_ENGINE
database.SessionLocal = TestingSessionLocal
database.Base = Base


def _create_test_database():
    """Create the test database if it doesn't exist."""
    # Connect to the default database to create test database
    base_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    temp_engine = create_engine(base_url, isolation_level="AUTOCOMMIT")

    with temp_engine.connect() as conn:
        # Check if test database exists
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'authapp_test'")
        )
        if not result.fetchone():
            conn.execute(text("CREATE DATABASE authapp_test"))

    temp_engine.dispose()


# Create test database if needed (only once at module load)
try:
    _create_test_database()
except Exception:
    pass  # Database may already exist or we're using a different setup


# Initialize schema once at module load
_schema_initialized = False


def _initialize_schema():
    """Initialize the database schema once."""
    global _schema_initialized
    if _schema_initialized:
        return

    # Drop all tables and recreate
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)
    _schema_initialized = True


# Initialize schema at module load
try:
    _initialize_schema()
except Exception as e:
    print(f"Warning: Could not initialize test schema: {e}")


# =============================================================================
# Core Fixtures
# =============================================================================


def override_get_db() -> Generator[Session, None, None]:
    """Yield a database session backed by the test engine."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency globally
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True, scope="function")
def setup_database(db_session: Session) -> Generator[None, None, None]:
    """
    Clean database for each test using truncation.

    Uses TRUNCATE CASCADE for speed instead of dropping/creating tables.
    """
    yield
    # Truncate all tables after test
    try:
        # Get all table names
        tables = Base.metadata.tables.keys()
        if tables:
            # Truncate all tables in one statement (faster)
            table_list = ", ".join(f'"{t}"' for t in tables)
            db_session.execute(text(f"TRUNCATE {table_list} CASCADE"))
            db_session.commit()
    except Exception:
        db_session.rollback()


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
        "/api/v1/auth/login",
        data={"username": admin_user.email, "password": "admin123"}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def tutor_token(client: TestClient, tutor_user: User) -> str:
    """Get tutor auth token via login."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": tutor_user.email, "password": "tutor123"}
    )
    assert response.status_code == 200, f"Tutor login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture
def student_token(client: TestClient, student_user: User) -> str:
    """Get student auth token via login."""
    response = client.post(
        "/api/v1/auth/login",
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


# =============================================================================
# Re-export commonly used fixtures for clarity
# =============================================================================

__all__ = [
    # Core fixtures
    "setup_database",
    "db_session",
    "db",
    "client",
    # User fixtures
    "admin_user",
    "tutor_user",
    "student_user",
    # Token fixtures (login-based)
    "admin_token",
    "tutor_token",
    "student_token",
    # Token fixtures (direct)
    "admin_token_direct",
    "tutor_token_direct",
    "student_token_direct",
    # Data fixtures
    "test_subject",
    "test_booking",
    # Legacy fixtures
    "test_student_token",
    "test_tutor_token",
    # Utility functions
    "create_test_user",
    "create_test_tutor_profile",
]
