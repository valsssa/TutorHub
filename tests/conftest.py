"""Shared pytest fixtures for saved tutor features."""

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the backend package is importable when tests are run from repo root
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Minimal, deterministic settings for tests
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-characters-long-123")
os.environ.setdefault("BCRYPT_ROUNDS", "4")  # speed up hashing in tests

import database  # noqa: E402
import models  # noqa: E402
from auth import get_password_hash  # noqa: E402
from core.security import TokenManager  # noqa: E402
from database import get_db  # noqa: E402
from main import app  # noqa: E402
from models import StudentProfile, TutorProfile, User  # noqa: E402

# SQLite in-memory database shared across connections
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

# Align global database state with the test engine and unified Base
database.engine = TEST_ENGINE
database.SessionLocal = TestingSessionLocal
database.Base = models.Base


def override_get_db() -> Generator[Session, None, None]:
    """Yield a database session backed by the test engine."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Create fresh schema for every test."""
    models.Base.metadata.drop_all(bind=TEST_ENGINE)
    models.Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    models.Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Direct access to the test session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(setup_database) -> Generator[TestClient, None, None]:
    """FastAPI test client with startup/shutdown lifecycle."""
    with TestClient(app) as test_client:
        yield test_client


def _ensure_student_profile(db: Session, user: User) -> None:
    """Create a student profile for the user if missing."""
    if user.role == "student" and not db.query(StudentProfile).filter_by(user_id=user.id).first():
        db.add(StudentProfile(user_id=user.id))
        db.commit()


def create_test_student(db: Session, email: str = "student@test.com", role: str = "student") -> User:
    """Create a test user (student by default)."""
    user = User(
        email=email.lower(),
        hashed_password=get_password_hash("password123"),
        role=role,
        is_verified=True,
        is_active=True,
        currency="USD",
        timezone="UTC",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _ensure_student_profile(db, user)
    return user


def create_test_tutor_profile(db: Session, user_id: int) -> TutorProfile:
    """Create a minimal approved tutor profile for the given user."""
    profile = TutorProfile(
        user_id=user_id,
        title="Test Tutor",
        headline="Expert tutor",
        bio="Passionate about teaching.",
        hourly_rate=50.00,
        experience_years=5,
        education="M.Ed.",
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


@pytest.fixture
def test_student_token(db: Session) -> str:
    """JWT for the default student (id expected to be 2 in tests)."""
    student = db.query(User).filter_by(email="student@example.com").first()
    if not student:
        # Seed admin first to ensure deterministic IDs
        if not db.query(User).filter_by(email="admin@example.com").first():
            admin = User(
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_verified=True,
                is_active=True,
                currency="USD",
                timezone="UTC",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        student = create_test_student(db, email="student@example.com")
    return TokenManager.create_access_token({"sub": student.email})


@pytest.fixture
def test_tutor_token(db: Session) -> str:
    """JWT for a tutor user."""
    tutor = db.query(User).filter_by(email="tutor@example.com").first()
    if not tutor:
        tutor = create_test_student(db, email="tutor@example.com", role="tutor")
    return TokenManager.create_access_token({"sub": tutor.email})
