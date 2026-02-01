"""Tests for favorites API endpoints."""

from fastapi import status

import pytest

from tests.conftest import STUDENT_PASSWORD


class TestGetFavorites:
    """Test GET /api/favorites endpoint."""

    def test_student_can_get_favorites(self, client, student_token):
        """Test student can retrieve favorites list."""
        response = client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_tutor_cannot_get_favorites(self, client, tutor_token):
        """Test tutor cannot access favorites (students only)."""
        response = client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "students" in response.json()["detail"].lower()

    def test_admin_cannot_get_favorites(self, client, admin_token):
        """Test admin cannot access favorites (students only)."""
        response = client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_get_favorites(self, client):
        """Test unauthenticated user cannot access favorites."""
        response = client.get("/api/v1/favorites")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAddFavorite:
    """Test POST /api/favorites endpoint."""

    def test_student_can_add_favorite(self, client, student_token, tutor_user):
        """Test student can add tutor to favorites."""
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["tutor_profile_id"] == tutor_user.tutor_profile.id

    def test_duplicate_favorite_returns_409(self, client, student_token, tutor_user):
        """Test adding same tutor twice returns conflict."""
        # Add first time
        client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )

        # Add second time - should fail
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already" in response.json()["detail"].lower()

    def test_nonexistent_tutor_returns_404(self, client, student_token):
        """Test adding nonexistent tutor returns 404."""
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": 99999},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_tutor_cannot_add_favorite(self, client, tutor_token, tutor_user):
        """Test tutor cannot add favorites."""
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_add_favorite(self, client, admin_token, tutor_user):
        """Test admin cannot add favorites."""
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_add_favorite(self, client, tutor_user):
        """Test unauthenticated user cannot add favorites."""
        response = client.post(
            "/api/v1/favorites",
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_tutor_profile_id(self, client, student_token):
        """Test missing tutor_profile_id returns 422."""
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRemoveFavorite:
    """Test DELETE /api/favorites/{tutor_profile_id} endpoint."""

    def test_student_can_remove_favorite(self, client, student_token, tutor_user, db_session):
        """Test student can remove tutor from favorites."""
        # First add favorite
        client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )

        # Then remove
        response = client.delete(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_remove_nonexistent_favorite_returns_404(self, client, student_token):
        """Test removing non-favorited tutor returns 404."""
        response = client.delete(
            "/api/v1/favorites/99999",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_tutor_cannot_remove_favorite(self, client, tutor_token, tutor_user):
        """Test tutor cannot remove favorites."""
        response = client.delete(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_remove_favorite(self, client, tutor_user):
        """Test unauthenticated user cannot remove favorites."""
        response = client.delete(f"/api/v1/favorites/{tutor_user.tutor_profile.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCheckFavorite:
    """Test GET /api/favorites/{tutor_profile_id} endpoint."""

    def test_check_existing_favorite(self, client, student_token, tutor_user):
        """Test checking if tutor is favorited (exists)."""
        # Add favorite first
        client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )

        # Check
        response = client.get(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["tutor_profile_id"] == tutor_user.tutor_profile.id

    def test_check_non_favorite_returns_404(self, client, student_token, tutor_user):
        """Test checking non-favorited tutor returns 404."""
        response = client.get(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_tutor_cannot_check_favorites(self, client, tutor_token, tutor_user):
        """Test tutor cannot check favorites."""
        response = client.get(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFavoritesIntegration:
    """Integration tests for favorites workflow."""

    def test_full_favorites_workflow(self, client, student_token, tutor_user):
        """Test complete favorites workflow: list -> add -> check -> remove."""
        tutor_id = tutor_user.tutor_profile.id

        # 1. List (empty)
        response = client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        initial_count = len(response.json())

        # 2. Add favorite
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"tutor_profile_id": tutor_id},
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 3. List (should have one more)
        response = client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert len(response.json()) == initial_count + 1

        # 4. Check specific favorite
        response = client.get(
            f"/api/v1/favorites/{tutor_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 5. Remove favorite
        response = client.delete(
            f"/api/v1/favorites/{tutor_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 6. Check again (should be 404)
        response = client.get(
            f"/api/v1/favorites/{tutor_id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # 7. List (back to original count)
        response = client.get(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert len(response.json()) == initial_count

    def test_favorites_persist(self, client, student_user, tutor_user, db_session):
        """Test that favorites persist across sessions."""
        tutor_id = tutor_user.tutor_profile.id

        # Login and add favorite
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": STUDENT_PASSWORD},
        )
        token1 = login_response.json()["access_token"]

        client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {token1}"},
            json={"tutor_profile_id": tutor_id},
        )

        # Login again
        login_response2 = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": STUDENT_PASSWORD},
        )
        token2 = login_response2.json()["access_token"]

        # Check favorite still exists
        response = client.get(
            f"/api/v1/favorites/{tutor_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == status.HTTP_200_OK
