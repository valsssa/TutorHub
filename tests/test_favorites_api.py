"""Test favorites API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.models import FavoriteTutor, User, TutorProfile
from tests.conftest import create_test_student, create_test_tutor_profile


def test_get_favorites_empty(client: TestClient, test_student_token: str):
    """Test getting favorites when user has no favorites."""
    response = client.get(
        "/api/favorites",
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_add_favorite_tutor(client: TestClient, test_student_token: str, db: Session):
    """Test adding a tutor to favorites."""
    # Create a test tutor profile
    tutor_user = create_test_student(db, email="tutor@test.com")
    tutor_profile = create_test_tutor_profile(db, tutor_user.id)

    response = client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == 2  # test student ID
    assert data["tutor_profile_id"] == tutor_profile.id

    # Verify in database
    favorite = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == 2,
        FavoriteTutor.tutor_profile_id == tutor_profile.id
    ).first()
    assert favorite is not None


def test_add_favorite_tutor_not_found(client: TestClient, test_student_token: str):
    """Test adding a non-existent tutor to favorites."""
    response = client.post(
        "/api/favorites",
        json={"tutor_profile_id": 9999},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 404
    assert "Tutor profile not found" in response.json()["detail"]


def test_add_favorite_duplicate(client: TestClient, test_student_token: str, db: Session):
    """Test adding the same tutor to favorites twice."""
    # Create a test tutor profile
    tutor_user = create_test_student(db, email="tutor@test.com")
    tutor_profile = create_test_tutor_profile(db, tutor_user.id)

    # Add first time
    response1 = client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )
    assert response1.status_code == 200

    # Try to add again
    response2 = client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )
    assert response2.status_code == 400
    assert "already in favorites" in response2.json()["detail"]


def test_get_favorites_with_data(client: TestClient, test_student_token: str, db: Session):
    """Test getting favorites when user has favorites."""
    # Create test tutor profiles
    tutor_user1 = create_test_student(db, email="tutor1@test.com")
    tutor_profile1 = create_test_tutor_profile(db, tutor_user1.id)

    tutor_user2 = create_test_student(db, email="tutor2@test.com")
    tutor_profile2 = create_test_tutor_profile(db, tutor_user2.id)

    # Add favorites
    client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile1.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )
    client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile2.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    response = client.get(
        "/api/favorites",
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["tutor_profile_id"] in [tutor_profile1.id, tutor_profile2.id]
    assert data[1]["tutor_profile_id"] in [tutor_profile1.id, tutor_profile2.id]


def test_remove_favorite_tutor(client: TestClient, test_student_token: str, db: Session):
    """Test removing a tutor from favorites."""
    # Create a test tutor profile
    tutor_user = create_test_student(db, email="tutor@test.com")
    tutor_profile = create_test_tutor_profile(db, tutor_user.id)

    # Add favorite first
    client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    # Remove favorite
    response = client.delete(
        f"/api/favorites/{tutor_profile.id}",
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "removed successfully" in data["message"]

    # Verify removed from database
    favorite = db.query(FavoriteTutor).filter(
        FavoriteTutor.student_id == 2,
        FavoriteTutor.tutor_profile_id == tutor_profile.id
    ).first()
    assert favorite is None


def test_remove_favorite_not_found(client: TestClient, test_student_token: str):
    """Test removing a tutor that is not in favorites."""
    response = client.delete(
        "/api/favorites/9999",
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_check_favorite_status(client: TestClient, test_student_token: str, db: Session):
    """Test checking if a tutor is in favorites."""
    # Create a test tutor profile
    tutor_user = create_test_student(db, email="tutor@test.com")
    tutor_profile = create_test_tutor_profile(db, tutor_user.id)

    # Add favorite
    client.post(
        "/api/favorites",
        json={"tutor_profile_id": tutor_profile.id},
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    # Check status
    response = client.get(
        f"/api/favorites/{tutor_profile.id}",
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == 2
    assert data["tutor_profile_id"] == tutor_profile.id


def test_check_favorite_status_not_found(client: TestClient, test_student_token: str, db: Session):
    """Test checking favorite status for a tutor not in favorites."""
    # Create a test tutor profile but don't add to favorites
    tutor_user = create_test_student(db, email="tutor@test.com")
    tutor_profile = create_test_tutor_profile(db, tutor_user.id)

    response = client.get(
        f"/api/favorites/{tutor_profile.id}",
        headers={"Authorization": f"Bearer {test_student_token}"}
    )

    assert response.status_code == 404
    assert "not in favorites" in response.json()["detail"]


def test_favorites_unauthorized(client: TestClient):
    """Test that favorites endpoints require authentication."""
    # Test all endpoints without auth
    endpoints = [
        ("GET", "/api/favorites"),
        ("POST", "/api/favorites"),
        ("DELETE", "/api/favorites/1"),
        ("GET", "/api/favorites/1"),
    ]

    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={"tutor_profile_id": 1})
        elif method == "DELETE":
            response = client.delete(endpoint)

        assert response.status_code == 401


def test_favorites_wrong_role(client: TestClient, test_tutor_token: str):
    """Test that only students can access favorites endpoints."""
    response = client.get(
        "/api/favorites",
        headers={"Authorization": f"Bearer {test_tutor_token}"}
    )

    assert response.status_code == 403