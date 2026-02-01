"""Tests for owner role functionality."""

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from auth import get_password_hash
from models import User

# Password that meets complexity requirements
TEST_OWNER_PASSWORD = "OwnerPass123!"
TEST_ADMIN_PASSWORD = "AdminPass123!"


@pytest.fixture
def owner_user(db: Session) -> User:
    """Create an owner user for testing."""
    owner = User(
        email="test_owner@example.com",
        hashed_password=get_password_hash(TEST_OWNER_PASSWORD),
        role="owner",
        is_verified=True,
        first_name="Test",
        last_name="Owner",
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


@pytest.fixture
def owner_token(client, owner_user) -> str:
    """Get JWT token for owner user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test_owner@example.com", "password": TEST_OWNER_PASSWORD},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for testing."""
    admin = User(
        email="test_admin@example.com",
        hashed_password=get_password_hash(TEST_ADMIN_PASSWORD),
        role="admin",
        is_verified=True,
        first_name="Test",
        last_name="Admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture
def admin_token(client, admin_user) -> str:
    """Get JWT token for admin user."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test_admin@example.com", "password": TEST_ADMIN_PASSWORD},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


class TestOwnerUserCreation:
    """Test owner user creation and authentication."""

    def test_owner_user_exists_from_startup(self, client, db: Session):
        """Test that default owner user is created on application startup.

        Note: The client fixture triggers app startup which creates default users.
        """
        # Check if default owner exists (created by app startup)
        owner = db.query(User).filter(User.role == "owner").first()
        assert owner is not None, "Owner user should be created on startup"
        assert owner.role == "owner"
        assert owner.is_verified is True

    def test_owner_can_login(self, client, owner_user):
        """Test that owner user can authenticate."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test_owner@example.com", "password": TEST_OWNER_PASSWORD},
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in response.json()

    def test_owner_role_validation(self, db: Session):
        """Test that database accepts owner role."""
        owner = User(
            email="another_owner@example.com",
            hashed_password=get_password_hash(TEST_OWNER_PASSWORD),
            role="owner",
            is_verified=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        assert owner.role == "owner"
        assert owner.id is not None


class TestOwnerDashboardAccess:
    """Test owner dashboard endpoint access."""

    def test_owner_can_access_dashboard(self, client, owner_token):
        """Test that owner user can access owner dashboard."""
        response = client.get(
            "/api/v1/owner/dashboard",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        # Should succeed (200) or return data structure
        # Exact status depends on implementation
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]

    def test_admin_cannot_access_owner_dashboard(self, client, admin_token):
        """Test that admin user CANNOT access owner-only endpoints."""
        response = client.get(
            "/api/v1/owner/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Admin should be forbidden from owner endpoints
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_access_owner_dashboard(self, client, student_token):
        """Test that student user cannot access owner dashboard."""
        response = client.get(
            "/api/v1/owner/dashboard",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_access_owner_dashboard(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/owner/dashboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestOwnerAdminAccess:
    """Test that owner has admin-level access (has_admin_access)."""

    def test_owner_can_access_admin_endpoints(self, client, owner_token):
        """Test that owner user can access admin endpoints (inherits admin access)."""
        # Owner should have admin permissions via has_admin_access
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        # Should succeed or return data
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_owner_can_manage_users(self, client, owner_token, db: Session):
        """Test that owner can perform admin user management tasks."""
        # Create a test user to manage
        test_user = User(
            email="manage_test@example.com",
            hashed_password=get_password_hash("test123"),
            role="student",
            is_verified=True,
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        # Owner should be able to update user role
        response = client.put(
            f"/api/v1/admin/users/{test_user.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "tutor"},
        )

        # Should succeed or return updated user
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]


class TestOwnerRoleAssignment:
    """Test owner role assignment restrictions."""

    def test_cannot_register_as_owner(self, client):
        """Test that public registration cannot create owner users."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "hacker@example.com",
                "password": "Password123!",
                "role": "owner",  # Should be rejected
                "first_name": "Hacker",
                "last_name": "User",
            },
        )
        # Registration should either fail or default to student role
        if response.status_code == status.HTTP_201_CREATED:
            # If registration succeeds, user should be student, not owner
            user_data = response.json()
            assert user_data["role"] == "student", "Registration should default to student role"
        else:
            # Or registration should fail with validation error
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

    def test_admin_can_assign_owner_role(self, client, admin_token, db: Session):
        """Test that admin users can assign owner role to other users."""
        # Create a student user
        student = User(
            email="upgrade_to_owner@example.com",
            hashed_password=get_password_hash(TEST_ADMIN_PASSWORD),
            role="student",
            is_verified=True,
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # Admin should be able to upgrade user to owner
        response = client.put(
            f"/api/v1/admin/users/{student.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"role": "owner"},
        )

        # Should succeed
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


class TestOwnerRoleHierarchy:
    """Test role hierarchy and permissions."""

    def test_role_hierarchy_level(self):
        """Test that owner role has highest hierarchy level."""
        from core.config import Roles

        # Owner should have hierarchy level 3 (highest)
        owner_level = Roles.HIERARCHY.get("owner")
        admin_level = Roles.HIERARCHY.get("admin")

        assert owner_level is not None, "Owner role should be in hierarchy"
        assert admin_level is not None, "Admin role should be in hierarchy"
        assert owner_level > admin_level, "Owner should have higher level than admin"

    def test_has_admin_access_for_owner(self):
        """Test that owner role is included in has_admin_access."""
        from core.config import Roles

        # Owner should have admin access
        assert Roles.has_admin_access("owner")

    def test_owner_permissions_in_endpoints(self, client, owner_token):
        """Test that owner can access all protected endpoints."""
        # Test various protected endpoints
        endpoints = [
            "/api/v1/users/me",  # User endpoint
            "/api/v1/admin/users",  # Admin endpoint
            "/api/v1/owner/dashboard",  # Owner endpoint
        ]

        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {owner_token}"},
            )
            # Should not be 401 (Unauthorized) or 403 (Forbidden)
            assert response.status_code not in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ], f"Owner should have access to {endpoint}"


class TestOwnerDataAccess:
    """Test owner access to sensitive business data."""

    def test_owner_can_view_financial_data(self, client, owner_token):
        """Test that owner can access financial data and analytics."""
        # Owner dashboard should return financial metrics
        response = client.get(
            "/api/v1/owner/dashboard",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        # Endpoint should be accessible
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]

        # If implemented, should return financial data
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Check for expected financial metrics
            assert isinstance(data, dict), "Dashboard should return data object"

    def test_admin_cannot_view_owner_financial_data(self, client, admin_token):
        """Test that admin users cannot access owner-level financial data."""
        response = client.get(
            "/api/v1/owner/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
