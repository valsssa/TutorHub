"""Tests for the favorites API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from modules.favorites.api import (
    add_favorite,
    check_favorite,
    get_favorites,
    remove_favorite,
)
from modules.favorites.schemas import FavoriteCreate


class TestGetFavorites:
    """Tests for the get_favorites endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def student_user(self):
        """Create mock student user."""
        user = MagicMock()
        user.id = 1
        user.role = "student"
        return user

    @pytest.fixture
    def tutor_user(self):
        """Create mock tutor user."""
        user = MagicMock()
        user.id = 2
        user.role = "tutor"
        return user

    @pytest.mark.asyncio
    async def test_get_favorites_success(self, mock_db, student_user):
        """Test getting favorites for a student."""
        mock_favorites = [
            MagicMock(id=1, student_id=1, tutor_profile_id=10),
            MagicMock(id=2, student_id=1, tutor_profile_id=20),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_favorites

        result = await get_favorites(student_user, mock_db)

        assert result == mock_favorites
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_favorites_empty(self, mock_db, student_user):
        """Test getting favorites when none exist."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await get_favorites(student_user, mock_db)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_favorites_forbidden_for_tutor(self, mock_db, tutor_user):
        """Test that tutors cannot have favorites."""
        with pytest.raises(HTTPException) as exc_info:
            await get_favorites(tutor_user, mock_db)

        assert exc_info.value.status_code == 403
        assert "students" in exc_info.value.detail.lower()


class TestAddFavorite:
    """Tests for the add_favorite endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def student_user(self):
        """Create mock student user."""
        user = MagicMock()
        user.id = 1
        user.role = "student"
        return user

    @pytest.fixture
    def tutor_user(self):
        """Create mock tutor user."""
        user = MagicMock()
        user.id = 2
        user.role = "tutor"
        return user

    @pytest.fixture
    def tutor_profile(self):
        """Create mock tutor profile."""
        profile = MagicMock()
        profile.id = 10
        return profile

    @pytest.mark.asyncio
    async def test_add_favorite_success(self, mock_db, student_user, tutor_profile):
        """Test adding a favorite successfully."""
        mock_db.query.return_value.filter.return_value.first.return_value = tutor_profile

        favorite_data = FavoriteCreate(tutor_profile_id=10)
        mock_favorite = MagicMock()
        mock_favorite.id = 1
        mock_favorite.student_id = 1
        mock_favorite.tutor_profile_id = 10

        with patch("modules.favorites.api.FavoriteTutor") as mock_favorite_tutor:
            mock_favorite_tutor.return_value = mock_favorite
            mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

            await add_favorite(favorite_data, student_user, mock_db)

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_favorite_forbidden_for_tutor(self, mock_db, tutor_user):
        """Test that tutors cannot add favorites."""
        favorite_data = FavoriteCreate(tutor_profile_id=10)

        with pytest.raises(HTTPException) as exc_info:
            await add_favorite(favorite_data, tutor_user, mock_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_add_favorite_tutor_not_found(self, mock_db, student_user):
        """Test adding favorite when tutor doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        favorite_data = FavoriteCreate(tutor_profile_id=999)

        with pytest.raises(HTTPException) as exc_info:
            await add_favorite(favorite_data, student_user, mock_db)

        assert exc_info.value.status_code == 404
        assert "tutor" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_add_favorite_duplicate(self, mock_db, student_user, tutor_profile):
        """Test adding a duplicate favorite."""
        mock_db.query.return_value.filter.return_value.first.return_value = tutor_profile
        mock_db.commit.side_effect = IntegrityError(None, None, None)

        favorite_data = FavoriteCreate(tutor_profile_id=10)

        with patch("modules.favorites.api.FavoriteTutor"):
            with pytest.raises(HTTPException) as exc_info:
                await add_favorite(favorite_data, student_user, mock_db)

            assert exc_info.value.status_code == 409
            assert "already" in exc_info.value.detail.lower()
            mock_db.rollback.assert_called_once()


class TestRemoveFavorite:
    """Tests for the remove_favorite endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def student_user(self):
        """Create mock student user."""
        user = MagicMock()
        user.id = 1
        user.role = "student"
        return user

    @pytest.fixture
    def tutor_user(self):
        """Create mock tutor user."""
        user = MagicMock()
        user.id = 2
        user.role = "tutor"
        return user

    @pytest.mark.asyncio
    async def test_remove_favorite_success(self, mock_db, student_user):
        """Test removing a favorite successfully."""
        mock_favorite = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_favorite

        await remove_favorite(10, student_user, mock_db)

        mock_db.delete.assert_called_once_with(mock_favorite)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_favorite_forbidden_for_tutor(self, mock_db, tutor_user):
        """Test that tutors cannot remove favorites."""
        with pytest.raises(HTTPException) as exc_info:
            await remove_favorite(10, tutor_user, mock_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_remove_favorite_not_found(self, mock_db, student_user):
        """Test removing a favorite that doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await remove_favorite(999, student_user, mock_db)

        assert exc_info.value.status_code == 404


class TestCheckFavorite:
    """Tests for the check_favorite endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def student_user(self):
        """Create mock student user."""
        user = MagicMock()
        user.id = 1
        user.role = "student"
        return user

    @pytest.fixture
    def tutor_user(self):
        """Create mock tutor user."""
        user = MagicMock()
        user.id = 2
        user.role = "tutor"
        return user

    @pytest.mark.asyncio
    async def test_check_favorite_exists(self, mock_db, student_user):
        """Test checking a favorite that exists."""
        mock_favorite = MagicMock()
        mock_favorite.id = 1
        mock_favorite.tutor_profile_id = 10
        mock_db.query.return_value.filter.return_value.first.return_value = mock_favorite

        result = await check_favorite(10, student_user, mock_db)

        assert result == mock_favorite

    @pytest.mark.asyncio
    async def test_check_favorite_not_found(self, mock_db, student_user):
        """Test checking a favorite that doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await check_favorite(999, student_user, mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_check_favorite_forbidden_for_tutor(self, mock_db, tutor_user):
        """Test that tutors cannot check favorites."""
        with pytest.raises(HTTPException) as exc_info:
            await check_favorite(10, tutor_user, mock_db)

        assert exc_info.value.status_code == 403


class TestFavoriteSchemas:
    """Tests for favorite schemas."""

    def test_favorite_create_valid(self):
        """Test creating a valid FavoriteCreate schema."""
        data = FavoriteCreate(tutor_profile_id=10)
        assert data.tutor_profile_id == 10

    def test_favorite_create_invalid_id(self):
        """Test FavoriteCreate rejects non-positive IDs."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            FavoriteCreate(tutor_profile_id=0)

        with pytest.raises(ValidationError):
            FavoriteCreate(tutor_profile_id=-1)
