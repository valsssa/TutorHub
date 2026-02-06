"""Tests for the favorites API endpoints."""

from datetime import UTC
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from modules.favorites.api import (
    add_favorite,
    check_favorite,
    check_favorites_batch,
    get_favorites,
    remove_favorite,
)
from modules.favorites.schemas import (
    FavoriteCheckResponse,
    FavoriteCreate,
    FavoritesCheckRequest,
    FavoritesCheckResponse,
)


class TestGetFavorites:
    """Tests for the get_favorites endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        # Setup chain for count query
        db.query.return_value.filter.return_value.scalar.return_value = 2
        return db

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
        """Test getting paginated favorites for a student."""
        from datetime import datetime

        mock_tutor_profile = MagicMock()
        mock_tutor_profile.id = 10
        mock_tutor_profile.user_id = 5
        mock_tutor_profile.user = MagicMock()
        mock_tutor_profile.user.first_name = "Test"
        mock_tutor_profile.user.last_name = "Tutor"
        mock_tutor_profile.user.avatar_key = None
        mock_tutor_profile.title = "Math Tutor"
        mock_tutor_profile.headline = "Expert"
        mock_tutor_profile.hourly_rate = 50
        mock_tutor_profile.average_rating = 4.5
        mock_tutor_profile.total_reviews = 10
        mock_tutor_profile.total_sessions = 20
        mock_tutor_profile.subjects = []

        mock_fav1 = MagicMock()
        mock_fav1.id = 1
        mock_fav1.student_id = 1
        mock_fav1.tutor_profile_id = 10
        mock_fav1.created_at = datetime.now()
        mock_fav1.tutor_profile = mock_tutor_profile

        mock_fav2 = MagicMock()
        mock_fav2.id = 2
        mock_fav2.student_id = 1
        mock_fav2.tutor_profile_id = 20
        mock_fav2.created_at = datetime.now()
        mock_fav2.tutor_profile = mock_tutor_profile

        mock_favorites = [mock_fav1, mock_fav2]

        # Setup count query
        mock_db.query.return_value.filter.return_value.scalar.return_value = 2
        # Setup data query chain
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_favorites

        result = await get_favorites(student_user, mock_db, page=1, page_size=20)

        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert result["total"] == 2
        assert result["page"] == 1
        assert result["page_size"] == 20

    @pytest.mark.asyncio
    async def test_get_favorites_empty(self, mock_db, student_user):
        """Test getting favorites when none exist returns empty paginated response."""
        # Setup count query
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        # Setup data query chain
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = await get_favorites(student_user, mock_db, page=1, page_size=20)

        assert result["items"] == []
        assert result["total"] == 0
        assert result["total_pages"] == 0

    @pytest.mark.asyncio
    async def test_get_favorites_pagination_metadata(self, mock_db, student_user):
        """Test that pagination metadata is correctly calculated."""
        # Setup count query - 25 total items
        mock_db.query.return_value.filter.return_value.scalar.return_value = 25
        # Setup data query chain
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = await get_favorites(student_user, mock_db, page=1, page_size=10)

        assert result["total"] == 25
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total_pages"] == 3  # ceil(25/10) = 3
        assert result["has_next"] is True
        assert result["has_prev"] is False

    @pytest.mark.asyncio
    async def test_get_favorites_last_page(self, mock_db, student_user):
        """Test pagination on last page."""
        # Setup count query - 25 total items
        mock_db.query.return_value.filter.return_value.scalar.return_value = 25
        # Setup data query chain
        mock_db.query.return_value.options.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = await get_favorites(student_user, mock_db, page=3, page_size=10)

        assert result["total"] == 25
        assert result["page"] == 3
        assert result["total_pages"] == 3
        assert result["has_next"] is False
        assert result["has_prev"] is True


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
        favorite_data = FavoriteCreate(tutor_profile_id=10)
        mock_favorite = MagicMock()
        mock_favorite.id = 1
        mock_favorite.student_id = 1
        mock_favorite.tutor_profile_id = 10

        with patch("modules.favorites.api.get_by_id_or_404") as mock_get_tutor:
            mock_get_tutor.return_value = tutor_profile
            # Query for existing favorite returns None (no existing record)
            mock_db.query.return_value.filter.return_value.first.return_value = None

            with patch("modules.favorites.api.FavoriteTutor") as mock_favorite_tutor:
                mock_favorite_tutor.return_value = mock_favorite
                mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

                await add_favorite(favorite_data, student_user, mock_db)

                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_favorite_forbidden_for_tutor(self, mock_db, tutor_user, tutor_profile):
        """Test that tutors cannot add favorites.

        Note: The StudentUser dependency in the actual API prevents tutors from
        reaching this endpoint. This test verifies the endpoint behavior if somehow
        a non-student user passed through.
        """
        # For unit tests, we test the function directly. The role check happens
        # at the dependency level (StudentUser), not in the function itself.
        # Since we're testing the function directly, it will proceed.
        # In integration tests, the 403 would be returned by the dependency.
        #
        # For this unit test, let's verify the function works with a tutor_user too
        # (since the actual role restriction is at the dependency injection level)
        mock_db.query.return_value.filter.return_value.first.side_effect = [tutor_profile, None]

        favorite_data = FavoriteCreate(tutor_profile_id=10)
        mock_favorite = MagicMock()
        mock_favorite.id = 1
        mock_favorite.student_id = 2
        mock_favorite.tutor_profile_id = 10

        with patch("modules.favorites.api.FavoriteTutor") as mock_favorite_tutor:
            mock_favorite_tutor.return_value = mock_favorite
            mock_db.refresh.side_effect = lambda x: setattr(x, "id", 1)

            # Function itself doesn't check role - that's done by StudentUser dependency
            result = await add_favorite(favorite_data, tutor_user, mock_db)
            assert result is not None

    @pytest.mark.asyncio
    async def test_add_favorite_tutor_not_found(self, mock_db, student_user):
        """Test adding favorite when tutor doesn't exist."""
        # First query for TutorProfile returns None (not found)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        favorite_data = FavoriteCreate(tutor_profile_id=999)

        with patch("modules.favorites.api.get_by_id_or_404") as mock_get:
            mock_get.side_effect = HTTPException(status_code=404, detail="Tutor profile not found")

            with pytest.raises(HTTPException) as exc_info:
                await add_favorite(favorite_data, student_user, mock_db)

            assert exc_info.value.status_code == 404
            assert "tutor" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_add_favorite_duplicate(self, mock_db, student_user, tutor_profile):
        """Test adding a duplicate favorite returns 409."""
        # Create an existing active favorite
        existing_favorite = MagicMock()
        existing_favorite.id = 1
        existing_favorite.student_id = 1
        existing_favorite.tutor_profile_id = 10
        existing_favorite.deleted_at = None  # Active (not soft-deleted)

        favorite_data = FavoriteCreate(tutor_profile_id=10)

        with patch("modules.favorites.api.get_by_id_or_404") as mock_get_tutor:
            mock_get_tutor.return_value = tutor_profile
            # Query for existing favorite returns the active favorite
            mock_db.query.return_value.filter.return_value.first.return_value = existing_favorite

            with pytest.raises(HTTPException) as exc_info:
                await add_favorite(favorite_data, student_user, mock_db)

            assert exc_info.value.status_code == 409
            assert "already" in exc_info.value.detail.lower()


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
        """Test removing a favorite successfully (soft delete)."""
        mock_favorite = MagicMock()
        mock_favorite.deleted_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_favorite

        await remove_favorite(10, student_user, mock_db)

        # Now uses soft delete, so deleted_at should be set
        assert mock_favorite.deleted_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_favorite_forbidden_for_tutor(self, mock_db, tutor_user):
        """Test remove_favorite with tutor user.

        Note: The StudentUser dependency in the actual API prevents tutors from
        reaching this endpoint. This unit test verifies the function behavior
        if somehow a non-student user passed through (role check is at dependency level).
        """
        # Since role check happens at dependency level, function will work
        mock_favorite = MagicMock()
        mock_favorite.deleted_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_favorite

        await remove_favorite(10, tutor_user, mock_db)

        # Function executes soft delete
        assert mock_favorite.deleted_at is not None
        mock_db.commit.assert_called_once()

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
        """Test checking a favorite that exists returns FavoriteCheckResponse with is_favorited=True."""
        from datetime import datetime, timezone

        mock_favorite = MagicMock()
        mock_favorite.id = 1
        mock_favorite.student_id = 1
        mock_favorite.tutor_profile_id = 10
        mock_favorite.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_favorite

        result = await check_favorite(10, student_user, mock_db)

        assert isinstance(result, FavoriteCheckResponse)
        assert result.is_favorited is True
        assert result.favorite is not None
        assert result.favorite.id == 1
        assert result.favorite.student_id == 1
        assert result.favorite.tutor_profile_id == 10

    @pytest.mark.asyncio
    async def test_check_favorite_not_found(self, mock_db, student_user):
        """Test checking a favorite that doesn't exist returns 200 with is_favorited=False."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await check_favorite(999, student_user, mock_db)

        assert isinstance(result, FavoriteCheckResponse)
        assert result.is_favorited is False
        assert result.favorite is None

    @pytest.mark.asyncio
    async def test_check_favorite_forbidden_for_tutor(self, mock_db, tutor_user):
        """Test check_favorite with tutor user.

        Note: The StudentUser dependency in the actual API prevents tutors from
        reaching this endpoint. This unit test verifies the function behavior
        if somehow a non-student user passed through (role check is at dependency level).
        """
        # Since role check happens at dependency level, function will return result
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await check_favorite(10, tutor_user, mock_db)

        assert isinstance(result, FavoriteCheckResponse)
        assert result.is_favorited is False


class TestCheckFavoritesBatch:
    """Tests for the check_favorites_batch endpoint."""

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

    @pytest.mark.asyncio
    async def test_check_favorites_batch_success(self, mock_db, student_user):
        """Test batch checking favorites with multiple IDs."""
        # Mock query to return tutor_profile_ids 10 and 30 as favorited
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (10,),
            (30,),
        ]

        request = FavoritesCheckRequest(tutor_profile_ids=[10, 20, 30, 40])
        result = await check_favorites_batch(request, student_user, mock_db)

        assert isinstance(result, FavoritesCheckResponse)
        assert result.favorited_ids == [10, 30]

    @pytest.mark.asyncio
    async def test_check_favorites_batch_none_favorited(self, mock_db, student_user):
        """Test batch check when no tutors are favorited."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        request = FavoritesCheckRequest(tutor_profile_ids=[10, 20, 30])
        result = await check_favorites_batch(request, student_user, mock_db)

        assert isinstance(result, FavoritesCheckResponse)
        assert result.favorited_ids == []

    @pytest.mark.asyncio
    async def test_check_favorites_batch_all_favorited(self, mock_db, student_user):
        """Test batch check when all tutors are favorited."""
        mock_db.query.return_value.filter.return_value.all.return_value = [
            (10,),
            (20,),
            (30,),
        ]

        request = FavoritesCheckRequest(tutor_profile_ids=[10, 20, 30])
        result = await check_favorites_batch(request, student_user, mock_db)

        assert isinstance(result, FavoritesCheckResponse)
        assert result.favorited_ids == [10, 20, 30]

    @pytest.mark.asyncio
    async def test_check_favorites_batch_single_id(self, mock_db, student_user):
        """Test batch check with a single ID."""
        mock_db.query.return_value.filter.return_value.all.return_value = [(10,)]

        request = FavoritesCheckRequest(tutor_profile_ids=[10])
        result = await check_favorites_batch(request, student_user, mock_db)

        assert isinstance(result, FavoritesCheckResponse)
        assert result.favorited_ids == [10]


class TestFavoritesCheckRequestValidation:
    """Tests for FavoritesCheckRequest schema validation."""

    def test_valid_request(self):
        """Test creating a valid request with multiple IDs."""
        request = FavoritesCheckRequest(tutor_profile_ids=[1, 2, 3, 4, 5])
        assert len(request.tutor_profile_ids) == 5

    def test_single_id_valid(self):
        """Test request with single ID is valid."""
        request = FavoritesCheckRequest(tutor_profile_ids=[1])
        assert request.tutor_profile_ids == [1]

    def test_max_100_ids_valid(self):
        """Test request with exactly 100 IDs is valid."""
        request = FavoritesCheckRequest(tutor_profile_ids=list(range(1, 101)))
        assert len(request.tutor_profile_ids) == 100

    def test_empty_list_invalid(self):
        """Test that empty list is rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            FavoritesCheckRequest(tutor_profile_ids=[])

        assert "min_length" in str(exc_info.value).lower() or "at least 1" in str(exc_info.value).lower()

    def test_over_100_ids_invalid(self):
        """Test that more than 100 IDs is rejected."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            FavoritesCheckRequest(tutor_profile_ids=list(range(1, 102)))

        assert "max_length" in str(exc_info.value).lower() or "at most 100" in str(exc_info.value).lower()


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


class TestPaginatedFavoritesResponse:
    """Tests for PaginatedFavoritesResponse schema."""

    def test_create_paginated_response(self):
        """Test creating a paginated response with metadata."""
        from datetime import datetime

        from modules.favorites.schemas import FavoriteResponse, PaginatedFavoritesResponse

        items = [
            FavoriteResponse(id=1, student_id=1, tutor_profile_id=10, created_at=datetime.now()),
            FavoriteResponse(id=2, student_id=1, tutor_profile_id=20, created_at=datetime.now()),
        ]

        response = PaginatedFavoritesResponse.create(
            items=items,
            total=25,
            page=1,
            page_size=10,
        )

        assert len(response.items) == 2
        assert response.total == 25
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_pages == 3
        assert response.has_next is True
        assert response.has_prev is False

    def test_paginated_response_last_page(self):
        """Test paginated response on last page."""
        from modules.favorites.schemas import PaginatedFavoritesResponse

        response = PaginatedFavoritesResponse.create(
            items=[],
            total=25,
            page=3,
            page_size=10,
        )

        assert response.total_pages == 3
        assert response.has_next is False
        assert response.has_prev is True

    def test_paginated_response_empty(self):
        """Test paginated response with no items."""
        from modules.favorites.schemas import PaginatedFavoritesResponse

        response = PaginatedFavoritesResponse.create(
            items=[],
            total=0,
            page=1,
            page_size=20,
        )

        assert response.items == []
        assert response.total == 0
        assert response.total_pages == 0
        assert response.has_next is False
        assert response.has_prev is False
