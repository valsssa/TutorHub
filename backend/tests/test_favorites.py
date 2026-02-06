"""Tests for favorites API endpoints."""

import pytest
from fastapi import status

from tests.conftest import STUDENT_PASSWORD, TUTOR_PASSWORD


@pytest.fixture
def student_auth(client, student_user):
    """Get student auth token and CSRF token via login."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": student_user.email, "password": STUDENT_PASSWORD}
    )
    assert response.status_code == 200, f"Student login failed: {response.text}"
    return {
        "token": response.json()["access_token"],
        "csrf": response.cookies.get("csrf_token"),
    }


@pytest.fixture
def tutor_auth(client, tutor_user):
    """Get tutor auth token and CSRF token via login."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": tutor_user.email, "password": TUTOR_PASSWORD}
    )
    assert response.status_code == 200, f"Tutor login failed: {response.text}"
    return {
        "token": response.json()["access_token"],
        "csrf": response.cookies.get("csrf_token"),
    }


def headers_for_get(auth):
    """Build headers for GET requests (no CSRF needed)."""
    return {"Authorization": f"Bearer {auth['token']}"}


def headers_for_unsafe(auth):
    """Build headers for POST/PUT/DELETE requests (CSRF required)."""
    headers = {"Authorization": f"Bearer {auth['token']}"}
    if auth.get("csrf"):
        headers["X-CSRF-Token"] = auth["csrf"]
    return headers


class TestGetFavorites:
    """Test GET /api/favorites endpoint."""

    def test_student_can_get_favorites(self, client, student_auth):
        """Test student can retrieve paginated favorites list."""
        response = client.get(
            "/api/v1/favorites",
            headers=headers_for_get(student_auth),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Check paginated response structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_prev" in data
        assert isinstance(data["items"], list)

    def test_student_can_get_favorites_with_pagination(self, client, student_auth):
        """Test student can retrieve favorites with custom pagination."""
        response = client.get(
            "/api/v1/favorites?page=1&page_size=10",
            headers=headers_for_get(student_auth),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_pagination_validates_max_page_size(self, client, student_auth):
        """Test that page_size is limited to 100."""
        response = client.get(
            "/api/v1/favorites?page_size=101",
            headers=headers_for_get(student_auth),
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_pagination_validates_min_page(self, client, student_auth):
        """Test that page must be at least 1."""
        response = client.get(
            "/api/v1/favorites?page=0",
            headers=headers_for_get(student_auth),
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_tutor_cannot_get_favorites(self, client, tutor_auth):
        """Test tutor cannot access favorites (students only)."""
        response = client.get(
            "/api/v1/favorites",
            headers=headers_for_get(tutor_auth),
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

    def test_student_can_add_favorite(self, client, student_auth, tutor_user):
        """Test student can add tutor to favorites."""
        response = client.post(
            "/api/v1/favorites",
            headers=headers_for_unsafe(student_auth),
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_201_CREATED, f"Response: {response.text}"
        data = response.json()
        assert data["tutor_profile_id"] == tutor_user.tutor_profile.id

    def test_duplicate_favorite_returns_409(self, client, student_auth, tutor_user):
        """Test adding same tutor twice returns conflict."""
        headers = headers_for_unsafe(student_auth)
        # Add first time
        client.post(
            "/api/v1/favorites",
            headers=headers,
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )

        # Add second time - should fail
        response = client.post(
            "/api/v1/favorites",
            headers=headers,
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already" in response.json()["detail"].lower()

    def test_nonexistent_tutor_returns_404(self, client, student_auth):
        """Test adding nonexistent tutor returns 404."""
        response = client.post(
            "/api/v1/favorites",
            headers=headers_for_unsafe(student_auth),
            json={"tutor_profile_id": 99999},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_tutor_cannot_add_favorite(self, client, tutor_auth, tutor_user):
        """Test tutor cannot add favorites."""
        response = client.post(
            "/api/v1/favorites",
            headers=headers_for_unsafe(tutor_auth),
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_add_favorite(self, client, admin_token, tutor_user):
        """Test admin cannot add favorites (no CSRF, but role check first)."""
        response = client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        # Will fail with CSRF error (403) before reaching role check
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_add_favorite(self, client, tutor_user):
        """Test unauthenticated user cannot add favorites."""
        response = client.post(
            "/api/v1/favorites",
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )
        # Will fail with CSRF error (403) - no token at all
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_missing_tutor_profile_id(self, client, student_auth):
        """Test missing tutor_profile_id returns 422."""
        response = client.post(
            "/api/v1/favorites",
            headers=headers_for_unsafe(student_auth),
            json={},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRemoveFavorite:
    """Test DELETE /api/favorites/{tutor_profile_id} endpoint."""

    def test_student_can_remove_favorite(self, client, student_auth, tutor_user, db_session):
        """Test student can remove tutor from favorites."""
        headers = headers_for_unsafe(student_auth)
        # First add favorite
        client.post(
            "/api/v1/favorites",
            headers=headers,
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )

        # Then remove
        response = client.delete(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers=headers,
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_remove_nonexistent_favorite_returns_404(self, client, student_auth):
        """Test removing non-favorited tutor returns 404."""
        response = client.delete(
            "/api/v1/favorites/99999",
            headers=headers_for_unsafe(student_auth),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_tutor_cannot_remove_favorite(self, client, tutor_auth, tutor_user):
        """Test tutor cannot remove favorites."""
        response = client.delete(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers=headers_for_unsafe(tutor_auth),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_remove_favorite(self, client, tutor_user):
        """Test unauthenticated user cannot remove favorites."""
        response = client.delete(f"/api/v1/favorites/{tutor_user.tutor_profile.id}")
        # Will fail with CSRF error (403)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCheckFavorite:
    """Test GET /api/favorites/{tutor_profile_id} endpoint."""

    def test_check_existing_favorite(self, client, student_auth, tutor_user):
        """Test checking if tutor is favorited (exists)."""
        # Add favorite first
        client.post(
            "/api/v1/favorites",
            headers=headers_for_unsafe(student_auth),
            json={"tutor_profile_id": tutor_user.tutor_profile.id},
        )

        # Check - now returns FavoriteCheckResponse with is_favorited=True
        response = client.get(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers=headers_for_get(student_auth),
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_favorited"] is True
        assert data["favorite"]["tutor_profile_id"] == tutor_user.tutor_profile.id

    def test_check_non_favorite_returns_200_not_favorited(self, client, student_auth, tutor_user):
        """Test checking non-favorited tutor returns 200 with is_favorited=False."""
        response = client.get(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers=headers_for_get(student_auth),
        )
        # New behavior: returns 200 with is_favorited=False instead of 404
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_favorited"] is False
        assert data["favorite"] is None

    def test_tutor_cannot_check_favorites(self, client, tutor_auth, tutor_user):
        """Test tutor cannot check favorites."""
        response = client.get(
            f"/api/v1/favorites/{tutor_user.tutor_profile.id}",
            headers=headers_for_get(tutor_auth),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFavoritesIntegration:
    """Integration tests for favorites workflow."""

    def test_full_favorites_workflow(self, client, student_auth, tutor_user):
        """Test complete favorites workflow: list -> add -> check -> remove."""
        tutor_id = tutor_user.tutor_profile.id
        get_headers = headers_for_get(student_auth)
        unsafe_headers = headers_for_unsafe(student_auth)

        # 1. List (empty)
        response = client.get("/api/v1/favorites", headers=get_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        initial_count = len(data["items"])
        initial_total = data["total"]

        # 2. Add favorite
        response = client.post(
            "/api/v1/favorites",
            headers=unsafe_headers,
            json={"tutor_profile_id": tutor_id},
        )
        assert response.status_code == status.HTTP_201_CREATED

        # 3. List (should have one more)
        response = client.get("/api/v1/favorites", headers=get_headers)
        data = response.json()
        assert len(data["items"]) == initial_count + 1
        assert data["total"] == initial_total + 1

        # 4. Check specific favorite - now returns FavoriteCheckResponse
        response = client.get(f"/api/v1/favorites/{tutor_id}", headers=get_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_favorited"] is True

        # 5. Remove favorite
        response = client.delete(f"/api/v1/favorites/{tutor_id}", headers=unsafe_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 6. Check again (should be 200 with is_favorited=False)
        response = client.get(f"/api/v1/favorites/{tutor_id}", headers=get_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_favorited"] is False

        # 7. List (back to original count)
        response = client.get("/api/v1/favorites", headers=get_headers)
        data = response.json()
        assert len(data["items"]) == initial_count
        assert data["total"] == initial_total

    def test_favorites_persist(self, client, student_user, tutor_user, db_session):
        """Test that favorites persist across sessions."""
        tutor_id = tutor_user.tutor_profile.id

        # Login and add favorite
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": STUDENT_PASSWORD},
        )
        token1 = login_response.json()["access_token"]
        csrf1 = login_response.cookies.get("csrf_token")

        client.post(
            "/api/v1/favorites",
            headers={"Authorization": f"Bearer {token1}", "X-CSRF-Token": csrf1},
            json={"tutor_profile_id": tutor_id},
        )

        # Login again
        login_response2 = client.post(
            "/api/v1/auth/login",
            data={"username": student_user.email, "password": STUDENT_PASSWORD},
        )
        token2 = login_response2.json()["access_token"]

        # Check favorite still exists - now returns FavoriteCheckResponse
        response = client.get(
            f"/api/v1/favorites/{tutor_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_favorited"] is True
