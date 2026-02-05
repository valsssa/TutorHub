"""Tests for public module domain layer.

Tests cover:
- Value objects (SearchQuery, SearchFilters, PaginationParams, SortOrder)
- Entities (PublicTutorProfileEntity, SearchResultEntity, SubjectInfo)
- Exceptions (PublicApiError, TutorProfileNotPublicError, etc.)
"""

from decimal import Decimal

import pytest

from modules.public.domain.entities import (
    PublicTutorProfileEntity,
    SearchResultEntity,
    SubjectInfo,
)
from modules.public.domain.exceptions import (
    InvalidSearchParametersError,
    PublicApiError,
    RateLimitExceededError,
    TutorProfileNotPublicError,
)
from modules.public.domain.value_objects import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_QUERY_LENGTH,
    MIN_PAGE,
    MIN_PAGE_SIZE,
    PaginationParams,
    SearchFilters,
    SearchQuery,
    SortOrder,
)


class TestSortOrder:
    """Tests for SortOrder enum."""

    def test_sort_order_values(self):
        """Test all sort order values exist."""
        assert SortOrder.RELEVANCE == "RELEVANCE"
        assert SortOrder.RATING == "RATING"
        assert SortOrder.PRICE_LOW == "PRICE_LOW"
        assert SortOrder.PRICE_HIGH == "PRICE_HIGH"
        assert SortOrder.NEWEST == "NEWEST"

    def test_sort_order_is_string(self):
        """Test sort order values are strings."""
        for sort_order in SortOrder:
            assert isinstance(sort_order.value, str)


class TestSearchQuery:
    """Tests for SearchQuery value object."""

    def test_search_query_valid(self):
        """Test creating valid search query."""
        query = SearchQuery(value="python programming")
        assert query.value == "python programming"

    def test_search_query_strips_whitespace(self):
        """Test that search query strips leading/trailing whitespace."""
        query = SearchQuery(value="  python   ")
        assert query.value == "python"

    def test_search_query_empty_string(self):
        """Test creating empty search query."""
        query = SearchQuery(value="")
        assert query.value == ""
        assert query.is_empty is True

    def test_search_query_whitespace_only(self):
        """Test creating whitespace-only search query."""
        query = SearchQuery(value="   ")
        assert query.value == ""
        assert query.is_empty is True

    def test_search_query_is_empty_property(self):
        """Test is_empty property."""
        query_empty = SearchQuery(value="")
        query_valid = SearchQuery(value="test")

        assert query_empty.is_empty is True
        assert query_valid.is_empty is False

    def test_search_query_str_method(self):
        """Test __str__ method returns query value."""
        query = SearchQuery(value="math tutor")
        assert str(query) == "math tutor"

    def test_search_query_max_length_exceeded(self):
        """Test that query exceeding max length raises error."""
        long_query = "a" * (MAX_QUERY_LENGTH + 1)

        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchQuery(value=long_query)

        assert exc_info.value.parameter == "query"
        assert "maximum length" in exc_info.value.reason.lower()

    def test_search_query_at_max_length(self):
        """Test that query at exactly max length is valid."""
        max_length_query = "a" * MAX_QUERY_LENGTH
        query = SearchQuery(value=max_length_query)
        assert len(query.value) == MAX_QUERY_LENGTH

    def test_search_query_immutable(self):
        """Test that SearchQuery is immutable (frozen dataclass)."""
        query = SearchQuery(value="test")
        with pytest.raises(AttributeError):
            query.value = "new value"


class TestSearchFilters:
    """Tests for SearchFilters value object."""

    def test_search_filters_all_none(self):
        """Test creating filters with all None values."""
        filters = SearchFilters()
        assert filters.subject_id is None
        assert filters.min_rating is None
        assert filters.max_price is None
        assert filters.availability is None
        assert filters.has_filters is False

    def test_search_filters_with_subject(self):
        """Test creating filters with subject ID."""
        filters = SearchFilters(subject_id=5)
        assert filters.subject_id == 5
        assert filters.has_filters is True

    def test_search_filters_with_min_rating(self):
        """Test creating filters with minimum rating."""
        filters = SearchFilters(min_rating=4.0)
        assert filters.min_rating == 4.0
        assert filters.has_filters is True

    def test_search_filters_with_max_price(self):
        """Test creating filters with maximum price."""
        filters = SearchFilters(max_price=5000)  # $50.00 in cents
        assert filters.max_price == 5000
        assert filters.has_filters is True

    def test_search_filters_with_availability_day(self):
        """Test creating filters with day of week availability."""
        for day in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]:
            filters = SearchFilters(availability=day)
            assert filters.availability == day
            assert filters.has_filters is True

    def test_search_filters_with_availability_time_period(self):
        """Test creating filters with time period availability."""
        for period in ["morning", "afternoon", "evening", "night"]:
            filters = SearchFilters(availability=period)
            assert filters.availability == period
            assert filters.has_filters is True

    def test_search_filters_with_availability_time_range(self):
        """Test creating filters with specific time range."""
        filters = SearchFilters(availability="09:00-17:00")
        assert filters.availability == "09:00-17:00"
        assert filters.has_filters is True

    def test_search_filters_invalid_subject_id_zero(self):
        """Test that zero subject ID raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(subject_id=0)

        assert exc_info.value.parameter == "subject_id"
        assert "positive" in exc_info.value.reason.lower()

    def test_search_filters_invalid_subject_id_negative(self):
        """Test that negative subject ID raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(subject_id=-1)

        assert exc_info.value.parameter == "subject_id"

    def test_search_filters_invalid_min_rating_too_low(self):
        """Test that rating below minimum raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(min_rating=-0.5)

        assert exc_info.value.parameter == "min_rating"

    def test_search_filters_invalid_min_rating_too_high(self):
        """Test that rating above maximum raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(min_rating=5.5)

        assert exc_info.value.parameter == "min_rating"

    def test_search_filters_valid_min_rating_bounds(self):
        """Test valid rating at boundaries."""
        filters_min = SearchFilters(min_rating=0.0)
        filters_max = SearchFilters(min_rating=5.0)

        assert filters_min.min_rating == 0.0
        assert filters_max.min_rating == 5.0

    def test_search_filters_invalid_max_price_zero(self):
        """Test that zero max price raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(max_price=0)

        assert exc_info.value.parameter == "max_price"

    def test_search_filters_invalid_max_price_negative(self):
        """Test that negative max price raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(max_price=-100)

        assert exc_info.value.parameter == "max_price"

    def test_search_filters_invalid_availability(self):
        """Test that invalid availability raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            SearchFilters(availability="invalid_day")

        assert exc_info.value.parameter == "availability"

    def test_search_filters_has_filters_property(self):
        """Test has_filters property with various combinations."""
        assert SearchFilters().has_filters is False
        assert SearchFilters(subject_id=1).has_filters is True
        assert SearchFilters(min_rating=4.0).has_filters is True
        assert SearchFilters(max_price=1000).has_filters is True
        assert SearchFilters(availability="monday").has_filters is True
        assert SearchFilters(subject_id=1, min_rating=4.0).has_filters is True


class TestPaginationParams:
    """Tests for PaginationParams value object."""

    def test_pagination_defaults(self):
        """Test default pagination values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == DEFAULT_PAGE_SIZE

    def test_pagination_custom_values(self):
        """Test custom pagination values."""
        params = PaginationParams(page=5, page_size=50)
        assert params.page == 5
        assert params.page_size == 50

    def test_pagination_offset_calculation(self):
        """Test offset calculation."""
        params_page_1 = PaginationParams(page=1, page_size=20)
        params_page_2 = PaginationParams(page=2, page_size=20)
        params_page_3 = PaginationParams(page=3, page_size=10)

        assert params_page_1.offset == 0
        assert params_page_2.offset == 20
        assert params_page_3.offset == 20

    def test_pagination_limit_property(self):
        """Test limit property equals page_size."""
        params = PaginationParams(page=1, page_size=25)
        assert params.limit == 25

    def test_pagination_default_factory(self):
        """Test default() class method."""
        params = PaginationParams.default()
        assert params.page == 1
        assert params.page_size == DEFAULT_PAGE_SIZE

    def test_pagination_invalid_page_zero(self):
        """Test that page 0 raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            PaginationParams(page=0)

        assert exc_info.value.parameter == "page"

    def test_pagination_invalid_page_negative(self):
        """Test that negative page raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            PaginationParams(page=-1)

        assert exc_info.value.parameter == "page"

    def test_pagination_invalid_page_size_zero(self):
        """Test that page_size 0 raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            PaginationParams(page_size=0)

        assert exc_info.value.parameter == "page_size"

    def test_pagination_invalid_page_size_negative(self):
        """Test that negative page_size raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            PaginationParams(page_size=-10)

        assert exc_info.value.parameter == "page_size"

    def test_pagination_invalid_page_size_exceeds_max(self):
        """Test that page_size exceeding max raises error."""
        with pytest.raises(InvalidSearchParametersError) as exc_info:
            PaginationParams(page_size=MAX_PAGE_SIZE + 1)

        assert exc_info.value.parameter == "page_size"

    def test_pagination_at_max_page_size(self):
        """Test pagination at exactly max page size."""
        params = PaginationParams(page_size=MAX_PAGE_SIZE)
        assert params.page_size == MAX_PAGE_SIZE

    def test_pagination_immutable(self):
        """Test that PaginationParams is immutable."""
        params = PaginationParams()
        with pytest.raises(AttributeError):
            params.page = 5


class TestSubjectInfo:
    """Tests for SubjectInfo entity."""

    def test_subject_info_basic(self):
        """Test creating basic SubjectInfo."""
        subject = SubjectInfo(id=1, name="Mathematics")
        assert subject.id == 1
        assert subject.name == "Mathematics"
        assert subject.category is None

    def test_subject_info_with_category(self):
        """Test SubjectInfo with category."""
        subject = SubjectInfo(id=2, name="Physics", category="Science")
        assert subject.id == 2
        assert subject.name == "Physics"
        assert subject.category == "Science"


class TestPublicTutorProfileEntity:
    """Tests for PublicTutorProfileEntity domain entity."""

    @pytest.fixture
    def basic_tutor(self):
        """Create a basic tutor entity for testing."""
        return PublicTutorProfileEntity(
            id=1,
            user_id=100,
            first_name="John",
            last_name="Smith",
            avatar_url="https://example.com/avatar.jpg",
            headline="Experienced Math Tutor",
            bio="10 years of teaching experience",
            subjects=[
                SubjectInfo(id=1, name="Math", category="STEM"),
                SubjectInfo(id=2, name="Physics", category="STEM"),
            ],
            average_rating=4.8,
            total_reviews=25,
            completed_sessions=150,
            hourly_rate_cents=5000,
            currency="USD",
            years_experience=10,
            response_time_hours=2,
            is_featured=True,
        )

    def test_tutor_display_name_with_last_name(self, basic_tutor):
        """Test display name includes first name and last initial."""
        assert basic_tutor.display_name == "John S."

    def test_tutor_display_name_without_last_name(self):
        """Test display name when no last name."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="John", last_name=None
        )
        assert tutor.display_name == "John"

    def test_tutor_full_name(self, basic_tutor):
        """Test full name property."""
        assert basic_tutor.full_name == "John Smith"

    def test_tutor_full_name_without_last_name(self):
        """Test full name when no last name."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="John", last_name=None
        )
        assert tutor.full_name == "John"

    def test_tutor_hourly_rate_decimal(self, basic_tutor):
        """Test hourly rate conversion to decimal."""
        assert basic_tutor.hourly_rate_decimal == Decimal("50.00")

    def test_tutor_hourly_rate_decimal_none(self):
        """Test hourly rate decimal when rate is None."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="John", hourly_rate_cents=None
        )
        assert tutor.hourly_rate_decimal is None

    def test_tutor_has_reviews_true(self, basic_tutor):
        """Test has_reviews when tutor has reviews."""
        assert basic_tutor.has_reviews is True

    def test_tutor_has_reviews_false(self):
        """Test has_reviews when tutor has no reviews."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="John", total_reviews=0
        )
        assert tutor.has_reviews is False

    def test_tutor_subject_names(self, basic_tutor):
        """Test subject_names property."""
        assert basic_tutor.subject_names == ["Math", "Physics"]

    def test_tutor_subject_names_empty(self):
        """Test subject_names when no subjects."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="John", subjects=[]
        )
        assert tutor.subject_names == []

    def test_tutor_initials_both_names(self, basic_tutor):
        """Test initials with both first and last name."""
        assert basic_tutor.initials == "JS"

    def test_tutor_initials_first_only(self):
        """Test initials with only first name."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="John", last_name=None
        )
        assert tutor.initials == "J"

    def test_tutor_initials_neither(self):
        """Test initials when no names (falls back to T)."""
        tutor = PublicTutorProfileEntity(
            id=1, user_id=100, first_name="", last_name=None
        )
        assert tutor.initials == "T"

    def test_tutor_default_values(self):
        """Test default values for optional fields."""
        tutor = PublicTutorProfileEntity(id=1, user_id=100, first_name="John")

        assert tutor.last_name is None
        assert tutor.avatar_url is None
        assert tutor.headline is None
        assert tutor.bio is None
        assert tutor.subjects == []
        assert tutor.average_rating is None
        assert tutor.total_reviews == 0
        assert tutor.completed_sessions == 0
        assert tutor.hourly_rate_cents is None
        assert tutor.currency == "USD"
        assert tutor.years_experience is None
        assert tutor.response_time_hours is None
        assert tutor.is_featured is False


class TestSearchResultEntity:
    """Tests for SearchResultEntity domain entity."""

    @pytest.fixture
    def tutors(self):
        """Create sample tutors for search results."""
        return [
            PublicTutorProfileEntity(id=1, user_id=100, first_name="John"),
            PublicTutorProfileEntity(id=2, user_id=101, first_name="Jane"),
            PublicTutorProfileEntity(id=3, user_id=102, first_name="Bob"),
        ]

    def test_search_result_basic(self, tutors):
        """Test creating search result."""
        result = SearchResultEntity(
            tutors=tutors, total_count=10, page=1, page_size=20
        )
        assert len(result.tutors) == 3
        assert result.total_count == 10
        assert result.page == 1
        assert result.page_size == 20

    def test_search_result_has_more_true(self, tutors):
        """Test has_more when there are more results."""
        result = SearchResultEntity(
            tutors=tutors, total_count=50, page=1, page_size=20
        )
        assert result.has_more is True

    def test_search_result_has_more_false(self, tutors):
        """Test has_more when no more results."""
        result = SearchResultEntity(
            tutors=tutors, total_count=3, page=1, page_size=20
        )
        assert result.has_more is False

    def test_search_result_has_more_on_last_page(self, tutors):
        """Test has_more on the last page."""
        result = SearchResultEntity(
            tutors=tutors, total_count=20, page=1, page_size=20
        )
        assert result.has_more is False

    def test_search_result_total_pages(self):
        """Test total_pages calculation."""
        result1 = SearchResultEntity(
            tutors=[], total_count=100, page=1, page_size=20
        )
        result2 = SearchResultEntity(
            tutors=[], total_count=21, page=1, page_size=20
        )
        result3 = SearchResultEntity(
            tutors=[], total_count=0, page=1, page_size=20
        )

        assert result1.total_pages == 5
        assert result2.total_pages == 2
        assert result3.total_pages == 0

    def test_search_result_total_pages_zero_page_size(self):
        """Test total_pages with zero page size."""
        result = SearchResultEntity(tutors=[], total_count=100, page=1, page_size=0)
        assert result.total_pages == 0

    def test_search_result_is_empty(self, tutors):
        """Test is_empty property."""
        empty_result = SearchResultEntity(
            tutors=[], total_count=0, page=1, page_size=20
        )
        non_empty_result = SearchResultEntity(
            tutors=tutors, total_count=3, page=1, page_size=20
        )

        assert empty_result.is_empty is True
        assert non_empty_result.is_empty is False

    def test_search_result_result_count(self, tutors):
        """Test result_count property."""
        result = SearchResultEntity(
            tutors=tutors, total_count=100, page=1, page_size=20
        )
        assert result.result_count == 3

    def test_search_result_empty_factory(self):
        """Test empty() class method."""
        result = SearchResultEntity.empty(page=2, page_size=10)

        assert result.tutors == []
        assert result.total_count == 0
        assert result.page == 2
        assert result.page_size == 10
        assert result.is_empty is True


class TestPublicApiError:
    """Tests for PublicApiError exception."""

    def test_public_api_error_basic(self):
        """Test creating basic PublicApiError."""
        error = PublicApiError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_public_api_error_is_base_class(self):
        """Test that other exceptions inherit from PublicApiError."""
        assert issubclass(TutorProfileNotPublicError, PublicApiError)
        assert issubclass(InvalidSearchParametersError, PublicApiError)
        assert issubclass(RateLimitExceededError, PublicApiError)


class TestTutorProfileNotPublicError:
    """Tests for TutorProfileNotPublicError exception."""

    def test_error_with_tutor_id(self):
        """Test error message includes tutor ID."""
        error = TutorProfileNotPublicError(tutor_id=123)
        assert error.tutor_id == 123
        assert "123" in str(error)
        assert "not publicly accessible" in str(error)

    def test_error_without_tutor_id(self):
        """Test error message without tutor ID."""
        error = TutorProfileNotPublicError()
        assert error.tutor_id is None
        assert "not publicly accessible" in str(error)


class TestInvalidSearchParametersError:
    """Tests for InvalidSearchParametersError exception."""

    def test_error_with_parameter_and_reason(self):
        """Test error with parameter name and reason."""
        error = InvalidSearchParametersError(
            parameter="subject_id", reason="Must be positive"
        )
        assert error.parameter == "subject_id"
        assert error.reason == "Must be positive"
        assert "subject_id" in str(error)
        assert "Must be positive" in str(error)

    def test_error_with_parameter_only(self):
        """Test error with only parameter name."""
        error = InvalidSearchParametersError(parameter="min_rating")
        assert error.parameter == "min_rating"
        assert "min_rating" in str(error)

    def test_error_with_reason_only(self):
        """Test error with only reason."""
        error = InvalidSearchParametersError(reason="Invalid format")
        assert error.reason == "Invalid format"
        assert "Invalid format" in str(error)

    def test_error_with_neither(self):
        """Test error with no specific details."""
        error = InvalidSearchParametersError()
        assert error.parameter is None
        assert error.reason is None
        assert "Invalid search parameters" in str(error)


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError exception."""

    def test_error_with_operation(self):
        """Test error with operation name."""
        error = RateLimitExceededError(operation="search")
        assert error.operation == "search"
        assert "search" in str(error)

    def test_error_with_retry_after(self):
        """Test error with retry after time."""
        error = RateLimitExceededError(operation="search", retry_after_seconds=60)
        assert error.operation == "search"
        assert error.retry_after_seconds == 60
        assert "60 seconds" in str(error)

    def test_error_defaults(self):
        """Test error with default values."""
        error = RateLimitExceededError()
        assert error.operation == "search"
        assert error.retry_after_seconds is None
