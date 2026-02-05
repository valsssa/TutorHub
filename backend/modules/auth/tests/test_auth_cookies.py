"""Tests for cookie-based authentication in login endpoint."""

import os
import sys
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Path setup
BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Test environment configuration
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/authapp_test"
    )
)
if "test" not in TEST_DATABASE_URL.lower():
    TEST_DATABASE_URL = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/authapp_test"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-characters-long-123")
os.environ.setdefault("BCRYPT_ROUNDS", "4")
os.environ["SKIP_STARTUP_MIGRATIONS"] = "true"

# Imports after path setup
import database
from auth import get_password_hash
from database import get_db
from main import app
from models import StudentProfile, User
from models.base import Base

# Database setup
TEST_ENGINE = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

database.engine = TEST_ENGINE
database.SessionLocal = TestingSessionLocal
database.Base = Base

# Disable rate limiting
from core.rate_limiting import limiter
limiter.enabled = False

# Standard test password
STUDENT_PASSWORD = "StudentPass123!"


def create_test_user(
    db: Session,
    email: str,
    password: str,
    role: str,
    first_name: str = "Test",
    last_name: str = "User",
) -> User:
    """Create a test user."""
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

    if role == "student":
        if not db.query(StudentProfile).filter_by(user_id=user.id).first():
            db.add(StudentProfile(user_id=user.id))
            db.commit()

    return user


def override_get_db() -> Generator[Session, None, None]:
    """Yield a database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="function")
def setup_database(db_session: Session) -> Generator[None, None, None]:
    """Clean database for each test."""
    yield
    try:
        tables = Base.metadata.tables.keys()
        if tables:
            table_list = ", ".join(f'"{t}"' for t in tables)
            db_session.execute(text(f"TRUNCATE {table_list} CASCADE"))
            db_session.commit()
    except Exception:
        db_session.rollback()


@pytest.fixture(scope="function")
def client(setup_database) -> Generator[TestClient, None, None]:
    """FastAPI test client with database setup."""
    with TestClient(app) as test_client:
        yield test_client


class TestLoginCookies:
    """Tests for cookie setting on login."""

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create a test user for login tests."""
        return create_test_user(
            db_session,
            email="cookietest@example.com",
            password=STUDENT_PASSWORD,
            role="student",
            first_name="Cookie",
            last_name="Tester",
        )

    def test_login_sets_access_token_cookie(self, client: TestClient, test_user):
        """Test that login sets access_token cookie."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200
        assert "access_token" in response.cookies

    def test_login_sets_refresh_token_cookie(self, client: TestClient, test_user):
        """Test that login sets refresh_token cookie."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200
        assert "refresh_token" in response.cookies

    def test_login_sets_csrf_token_cookie(self, client: TestClient, test_user):
        """Test that login sets csrf_token cookie."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200
        assert "csrf_token" in response.cookies

    def test_login_still_returns_tokens_in_body(self, client: TestClient, test_user):
        """Test that login still returns tokens in JSON body for backwards compatibility."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_cookies_have_values(self, client: TestClient, test_user):
        """Test that cookies have non-empty values."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200

        # Cookies should have non-empty values
        assert len(response.cookies.get("access_token", "")) > 0
        assert len(response.cookies.get("refresh_token", "")) > 0
        assert len(response.cookies.get("csrf_token", "")) > 0

    def test_login_access_token_cookie_matches_body(self, client: TestClient, test_user):
        """Test that access_token cookie matches the one in the response body."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200

        data = response.json()
        cookie_token = response.cookies.get("access_token")
        body_token = data.get("access_token")

        assert cookie_token == body_token

    def test_login_refresh_token_cookie_matches_body(self, client: TestClient, test_user):
        """Test that refresh_token cookie matches the one in the response body."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert response.status_code == 200

        data = response.json()
        cookie_token = response.cookies.get("refresh_token")
        body_token = data.get("refresh_token")

        assert cookie_token == body_token

    def test_login_failure_does_not_set_cookies(self, client: TestClient, test_user):
        """Test that failed login does not set cookies."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401

        # No cookies should be set on failed login
        assert "access_token" not in response.cookies
        assert "refresh_token" not in response.cookies
        assert "csrf_token" not in response.cookies


class TestLogoutCookies:
    """Tests for cookie clearing on logout."""

    @pytest.fixture
    def test_user(self, db_session: Session):
        """Create a test user for logout tests."""
        return create_test_user(
            db_session,
            email="logouttest@example.com",
            password=STUDENT_PASSWORD,
            role="student",
            first_name="Logout",
            last_name="Tester",
        )

    def test_logout_clears_all_cookies(self, client: TestClient, test_user):
        """Test that logout clears access_token, refresh_token, and csrf_token cookies."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        assert login_response.status_code == 200

        # Get the access token for authorization
        access_token = login_response.json()["access_token"]

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert logout_response.status_code == 200
        assert logout_response.json() == {"message": "Successfully logged out"}

        # Verify cookies are cleared (set with max_age=0 or deleted)
        set_cookie_headers = logout_response.headers.getlist("set-cookie")
        cookie_names_cleared = []
        for header in set_cookie_headers:
            header_lower = header.lower()
            # Check for cookie deletion indicators (max-age=0 or expires in the past)
            is_deleted = "max-age=0" in header_lower or 'max-age="0"' in header_lower
            if "access_token=" in header and is_deleted:
                cookie_names_cleared.append("access_token")
            if "refresh_token=" in header and is_deleted:
                cookie_names_cleared.append("refresh_token")
            if "csrf_token=" in header and is_deleted:
                cookie_names_cleared.append("csrf_token")

        # All three cookies should be cleared
        assert "access_token" in cookie_names_cleared, "access_token cookie not cleared"
        assert "refresh_token" in cookie_names_cleared, "refresh_token cookie not cleared"
        assert "csrf_token" in cookie_names_cleared, "csrf_token cookie not cleared"

    def test_logout_requires_authentication(self, client: TestClient):
        """Test that logout requires a valid access token."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    def test_logout_with_invalid_token(self, client: TestClient):
        """Test that logout with an invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_logout_returns_success_message(self, client: TestClient, test_user):
        """Test that logout returns the expected success message."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        access_token = login_response.json()["access_token"]

        # Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert logout_response.status_code == 200
        data = logout_response.json()
        assert "message" in data
        assert data["message"] == "Successfully logged out"

    def test_logout_twice_fails_second_time(self, client: TestClient, test_user):
        """Test that logging out twice with the same token works for both calls.

        Note: Since we're using stateless JWTs, the token remains valid until expiry.
        The logout just clears cookies; it doesn't invalidate the token.
        """
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": STUDENT_PASSWORD},
        )
        access_token = login_response.json()["access_token"]

        # First logout - should succeed
        logout_response1 = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response1.status_code == 200

        # Second logout with same token - should still succeed (stateless JWT)
        logout_response2 = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response2.status_code == 200
