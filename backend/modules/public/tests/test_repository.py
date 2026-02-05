"""Tests for public module infrastructure repository.

Tests cover:
- PublicTutorRepositoryImpl search operations
- Featured tutors retrieval
- Subject-based queries
- Sorting and pagination
"""

from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from modules.public.domain.entities import (
    PublicTutorProfileEntity,
    SearchResultEntity,
)
from modules.public.domain.value_objects import (
    PaginationParams,
    SearchFilters,
    SearchQuery,
    SortOrder,
)
from modules.public.infrastructure.repositories import PublicTutorRepositoryImpl


class TestPublicTutorRepositoryImpl:
    """Tests for PublicTutorRepositoryImpl."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile


class TestSearch:
    """Tests for search method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile

    def test_search_with_defaults(self, repository, mock_db, mock_tutor_profile):
        """Test search with default parameters."""
        # Set up mock query chain
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.search()

        assert isinstance(result, SearchResultEntity)
        assert result.total_count == 1
        assert result.page == 1
        assert len(result.tutors) == 1

    def test_search_with_query(self, repository, mock_db, mock_tutor_profile):
        """Test search with text query."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        search_query = SearchQuery(value="math")
        result = repository.search(query=search_query)

        assert isinstance(result, SearchResultEntity)

    def test_search_with_filters(self, repository, mock_db, mock_tutor_profile):
        """Test search with filters."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        filters = SearchFilters(min_rating=4.0, max_price=10000)
        result = repository.search(filters=filters)

        assert isinstance(result, SearchResultEntity)

    def test_search_with_pagination(self, repository, mock_db, mock_tutor_profile):
        """Test search with custom pagination."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 50
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        pagination = PaginationParams(page=2, page_size=10)
        result = repository.search(pagination=pagination)

        assert result.page == 2
        assert result.page_size == 10
        assert result.total_count == 50

    def test_search_with_sort_by_rating(self, repository, mock_db, mock_tutor_profile):
        """Test search sorted by rating."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.search(sort_by=SortOrder.RATING)

        assert isinstance(result, SearchResultEntity)

    def test_search_with_sort_by_price_low(self, repository, mock_db, mock_tutor_profile):
        """Test search sorted by price low to high."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.search(sort_by=SortOrder.PRICE_LOW)

        assert isinstance(result, SearchResultEntity)

    def test_search_with_sort_by_price_high(self, repository, mock_db, mock_tutor_profile):
        """Test search sorted by price high to low."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.search(sort_by=SortOrder.PRICE_HIGH)

        assert isinstance(result, SearchResultEntity)

    def test_search_with_sort_by_newest(self, repository, mock_db, mock_tutor_profile):
        """Test search sorted by newest."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.search(sort_by=SortOrder.NEWEST)

        assert isinstance(result, SearchResultEntity)

    def test_search_empty_results(self, repository, mock_db):
        """Test search with no results."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []

        mock_db.query.return_value = query_mock

        result = repository.search()

        assert result.total_count == 0
        assert len(result.tutors) == 0
        assert result.is_empty is True


class TestGetPublicProfile:
    """Tests for get_public_profile method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile

    def test_get_public_profile_found(self, repository, mock_db, mock_tutor_profile):
        """Test getting a public profile that exists."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.first.return_value = mock_tutor_profile

        mock_db.query.return_value = query_mock

        result = repository.get_public_profile(tutor_id=1)

        assert result is not None
        assert isinstance(result, PublicTutorProfileEntity)
        assert result.id == 1

    def test_get_public_profile_not_found(self, repository, mock_db):
        """Test getting a profile that doesn't exist."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.first.return_value = None

        mock_db.query.return_value = query_mock

        result = repository.get_public_profile(tutor_id=999)

        assert result is None


class TestGetPublicProfileByUserId:
    """Tests for get_public_profile_by_user_id method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile

    def test_get_by_user_id_found(self, repository, mock_db, mock_tutor_profile):
        """Test getting a profile by user ID that exists."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.first.return_value = mock_tutor_profile

        mock_db.query.return_value = query_mock

        result = repository.get_public_profile_by_user_id(user_id=100)

        assert result is not None
        assert isinstance(result, PublicTutorProfileEntity)
        assert result.user_id == 100

    def test_get_by_user_id_not_found(self, repository, mock_db):
        """Test getting a profile by user ID that doesn't exist."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.first.return_value = None

        mock_db.query.return_value = query_mock

        result = repository.get_public_profile_by_user_id(user_id=999)

        assert result is None


class TestGetFeatured:
    """Tests for get_featured method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile

    def test_get_featured_success(self, repository, mock_db, mock_tutor_profile):
        """Test getting featured tutors."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.get_featured(limit=6)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], PublicTutorProfileEntity)

    def test_get_featured_respects_limit(self, repository, mock_db, mock_tutor_profile):
        """Test get_featured respects the limit parameter."""
        profiles = [mock_tutor_profile] * 3

        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = profiles

        mock_db.query.return_value = query_mock

        result = repository.get_featured(limit=3)

        assert len(result) == 3

    def test_get_featured_empty(self, repository, mock_db):
        """Test get_featured with no featured tutors."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []

        mock_db.query.return_value = query_mock

        result = repository.get_featured(limit=6)

        assert result == []


class TestGetBySubject:
    """Tests for get_by_subject method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile

    def test_get_by_subject_found(self, repository, mock_db, mock_tutor_profile):
        """Test getting tutors for a subject."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 1
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.get_by_subject(subject_id=1)

        assert isinstance(result, SearchResultEntity)
        assert result.total_count == 1
        assert len(result.tutors) == 1

    def test_get_by_subject_empty(self, repository, mock_db):
        """Test getting tutors for a subject with no tutors."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 0
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []

        mock_db.query.return_value = query_mock

        result = repository.get_by_subject(subject_id=999)

        assert result.total_count == 0
        assert len(result.tutors) == 0

    def test_get_by_subject_with_pagination(
        self, repository, mock_db, mock_tutor_profile
    ):
        """Test get_by_subject with pagination."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 50
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        pagination = PaginationParams(page=2, page_size=10)
        result = repository.get_by_subject(subject_id=1, pagination=pagination)

        assert result.page == 2
        assert result.page_size == 10


class TestGetTopRated:
    """Tests for get_top_rated method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    @pytest.fixture
    def mock_tutor_profile(self):
        """Create a mock TutorProfile model."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Experienced Math Tutor"
        profile.bio = "10 years teaching experience"
        profile.average_rating = Decimal("4.8")
        profile.total_reviews = 25
        profile.total_sessions = 150
        profile.hourly_rate = Decimal("50.00")
        profile.currency = "USD"
        profile.experience_years = 10
        profile.subjects = []

        # Mock user relationship
        profile.user = MagicMock()
        profile.user.first_name = "John"
        profile.user.last_name = "Smith"
        profile.user.avatar_key = None

        return profile

    def test_get_top_rated_success(self, repository, mock_db, mock_tutor_profile):
        """Test getting top rated tutors."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [mock_tutor_profile]

        mock_db.query.return_value = query_mock

        result = repository.get_top_rated(limit=10, min_reviews=3)

        assert isinstance(result, list)
        assert len(result) == 1

    def test_get_top_rated_empty(self, repository, mock_db):
        """Test get_top_rated when no tutors meet criteria."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = []

        mock_db.query.return_value = query_mock

        result = repository.get_top_rated(limit=10, min_reviews=100)

        assert result == []


class TestCountBySubject:
    """Tests for count_by_subject method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    def test_count_by_subject_found(self, repository, mock_db):
        """Test counting tutors for a subject."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 15

        mock_db.query.return_value = query_mock

        result = repository.count_by_subject(subject_id=1)

        assert result == 15

    def test_count_by_subject_zero(self, repository, mock_db):
        """Test counting tutors for a subject with none."""
        query_mock = MagicMock()
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.count.return_value = 0

        mock_db.query.return_value = query_mock

        result = repository.count_by_subject(subject_id=999)

        assert result == 0


class TestGetSubjectsWithTutors:
    """Tests for get_subjects_with_tutors method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    def test_get_subjects_with_tutors_success(self, repository, mock_db):
        """Test getting subjects with tutor counts."""
        # Mock subquery
        subquery_mock = MagicMock()
        subquery_mock.subquery.return_value = subquery_mock

        # Mock main query
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.having.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [
            (1, "Mathematics", 25),
            (2, "Physics", 15),
            (3, "Chemistry", 10),
        ]

        mock_db.query.return_value = query_mock

        result = repository.get_subjects_with_tutors()

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0] == (1, "Mathematics", 25)
        assert result[1] == (2, "Physics", 15)
        assert result[2] == (3, "Chemistry", 10)

    def test_get_subjects_with_tutors_empty(self, repository, mock_db):
        """Test getting subjects when none have tutors."""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.having.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = []

        mock_db.query.return_value = query_mock

        result = repository.get_subjects_with_tutors()

        assert result == []


class TestToPublicEntity:
    """Tests for _to_public_entity conversion method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository instance with mock db."""
        return PublicTutorRepositoryImpl(mock_db)

    def test_to_public_entity_basic(self, repository):
        """Test converting a basic tutor profile to entity."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = "Math Tutor"
        profile.bio = "Teaching math for years"
        profile.average_rating = Decimal("4.5")
        profile.total_reviews = 10
        profile.total_sessions = 50
        profile.hourly_rate = Decimal("40.00")
        profile.currency = "USD"
        profile.experience_years = 5
        profile.subjects = []

        profile.user = MagicMock()
        profile.user.first_name = "Jane"
        profile.user.last_name = "Doe"
        profile.user.avatar_key = None

        result = repository._to_public_entity(profile)

        assert result.id == 1
        assert result.user_id == 100
        assert result.first_name == "Jane"
        assert result.last_name == "Doe"
        assert result.headline == "Math Tutor"
        assert result.average_rating == 4.5
        assert result.total_reviews == 10
        assert result.completed_sessions == 50
        assert result.hourly_rate_cents == 4000
        assert result.currency == "USD"

    def test_to_public_entity_no_user(self, repository):
        """Test converting profile without user relationship."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = None
        profile.bio = None
        profile.average_rating = None
        profile.total_reviews = None
        profile.total_sessions = None
        profile.hourly_rate = None
        profile.currency = None
        profile.experience_years = None
        profile.subjects = []
        profile.user = None

        result = repository._to_public_entity(profile)

        assert result.first_name == ""
        assert result.last_name is None
        assert result.avatar_url is None

    def test_to_public_entity_featured_status(self, repository):
        """Test featured status calculation."""
        # Profile that should be featured (5+ reviews, 4.5+ rating)
        featured_profile = MagicMock()
        featured_profile.id = 1
        featured_profile.user_id = 100
        featured_profile.headline = None
        featured_profile.bio = None
        featured_profile.average_rating = Decimal("4.8")
        featured_profile.total_reviews = 10
        featured_profile.total_sessions = 50
        featured_profile.hourly_rate = None
        featured_profile.currency = None
        featured_profile.experience_years = None
        featured_profile.subjects = []
        featured_profile.user = MagicMock()
        featured_profile.user.first_name = "John"
        featured_profile.user.last_name = None
        featured_profile.user.avatar_key = None

        result = repository._to_public_entity(featured_profile)
        assert result.is_featured is True

        # Profile that should NOT be featured (less than 5 reviews)
        not_featured_profile = MagicMock()
        not_featured_profile.id = 2
        not_featured_profile.user_id = 101
        not_featured_profile.headline = None
        not_featured_profile.bio = None
        not_featured_profile.average_rating = Decimal("4.9")
        not_featured_profile.total_reviews = 3
        not_featured_profile.total_sessions = 10
        not_featured_profile.hourly_rate = None
        not_featured_profile.currency = None
        not_featured_profile.experience_years = None
        not_featured_profile.subjects = []
        not_featured_profile.user = MagicMock()
        not_featured_profile.user.first_name = "Jane"
        not_featured_profile.user.last_name = None
        not_featured_profile.user.avatar_key = None

        result2 = repository._to_public_entity(not_featured_profile)
        assert result2.is_featured is False

    def test_to_public_entity_with_subjects(self, repository):
        """Test converting profile with subjects."""
        profile = MagicMock()
        profile.id = 1
        profile.user_id = 100
        profile.headline = None
        profile.bio = None
        profile.average_rating = None
        profile.total_reviews = 0
        profile.total_sessions = 0
        profile.hourly_rate = None
        profile.currency = "USD"
        profile.experience_years = None
        profile.user = MagicMock()
        profile.user.first_name = "Test"
        profile.user.last_name = "User"
        profile.user.avatar_key = None

        # Create mock subject relationships
        subject1 = MagicMock()
        subject1.subject = MagicMock()
        subject1.subject.id = 1
        subject1.subject.name = "Math"
        subject1.subject.category = "STEM"

        subject2 = MagicMock()
        subject2.subject = MagicMock()
        subject2.subject.id = 2
        subject2.subject.name = "Physics"
        subject2.subject.category = "STEM"

        profile.subjects = [subject1, subject2]

        result = repository._to_public_entity(profile)

        assert len(result.subjects) == 2
        assert result.subjects[0].name == "Math"
        assert result.subjects[1].name == "Physics"
