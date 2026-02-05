"""Tests for the public API router endpoints.

Tests cover:
- GET /public/stats - Platform statistics
- GET /public/featured-reviews - Featured reviews for testimonials
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from modules.public.router import (
    FeaturedReview,
    FeaturedReviewsResponse,
    PlatformStats,
    get_featured_reviews,
    get_platform_stats,
)


class TestGetPlatformStats:
    """Tests for the get_platform_stats endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_platform_stats_success(self, mock_db):
        """Test getting platform stats successfully with data."""
        # Set up mock query chain for tutor count
        tutor_query = MagicMock()
        tutor_query.filter.return_value.filter.return_value.count.return_value = 15

        # Set up mock query chain for student count
        student_query = MagicMock()
        student_query.filter.return_value.filter.return_value.count.return_value = 100

        # Set up mock query chain for average rating
        avg_rating_query = MagicMock()
        avg_rating_query.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = (
            Decimal("4.7")
        )

        # Set up mock query chain for completed sessions
        sessions_query = MagicMock()
        sessions_query.filter.return_value.filter.return_value.filter.return_value.count.return_value = (
            500
        )

        # Configure mock_db.query to return different mocks based on the model
        query_calls = [tutor_query, student_query, avg_rating_query, sessions_query]
        mock_db.query.side_effect = query_calls

        result = await get_platform_stats(mock_db)

        assert isinstance(result, PlatformStats)
        assert result.tutor_count == 15
        assert result.student_count == 100
        assert result.average_rating == 4.7
        assert result.completed_sessions == 500
        assert isinstance(result.generated_at, datetime)

    @pytest.mark.asyncio
    async def test_get_platform_stats_empty_database(self, mock_db):
        """Test getting platform stats when database has no data."""
        # Set up mock query chain for tutor count
        tutor_query = MagicMock()
        tutor_query.filter.return_value.filter.return_value.count.return_value = 0

        # Set up mock query chain for student count
        student_query = MagicMock()
        student_query.filter.return_value.filter.return_value.count.return_value = 0

        # Set up mock query chain for average rating (no ratings)
        avg_rating_query = MagicMock()
        avg_rating_query.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = (
            None
        )

        # Set up mock query chain for completed sessions
        sessions_query = MagicMock()
        sessions_query.filter.return_value.filter.return_value.filter.return_value.count.return_value = (
            0
        )

        query_calls = [tutor_query, student_query, avg_rating_query, sessions_query]
        mock_db.query.side_effect = query_calls

        result = await get_platform_stats(mock_db)

        assert isinstance(result, PlatformStats)
        assert result.tutor_count == 0
        assert result.student_count == 0
        # Should default to 4.8 when no ratings
        assert result.average_rating == 4.8
        assert result.completed_sessions == 0

    @pytest.mark.asyncio
    async def test_get_platform_stats_rating_precision(self, mock_db):
        """Test that average rating is rounded to one decimal place."""
        tutor_query = MagicMock()
        tutor_query.filter.return_value.filter.return_value.count.return_value = 10

        student_query = MagicMock()
        student_query.filter.return_value.filter.return_value.count.return_value = 50

        # Average rating with many decimals
        avg_rating_query = MagicMock()
        avg_rating_query.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = (
            Decimal("4.666666666666667")
        )

        sessions_query = MagicMock()
        sessions_query.filter.return_value.filter.return_value.filter.return_value.count.return_value = (
            200
        )

        query_calls = [tutor_query, student_query, avg_rating_query, sessions_query]
        mock_db.query.side_effect = query_calls

        result = await get_platform_stats(mock_db)

        # Should be rounded to 4.7
        assert result.average_rating == 4.7

    @pytest.mark.asyncio
    async def test_get_platform_stats_large_numbers(self, mock_db):
        """Test platform stats with large numbers."""
        tutor_query = MagicMock()
        tutor_query.filter.return_value.filter.return_value.count.return_value = 10000

        student_query = MagicMock()
        student_query.filter.return_value.filter.return_value.count.return_value = (
            500000
        )

        avg_rating_query = MagicMock()
        avg_rating_query.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = (
            Decimal("4.9")
        )

        sessions_query = MagicMock()
        sessions_query.filter.return_value.filter.return_value.filter.return_value.count.return_value = (
            1000000
        )

        query_calls = [tutor_query, student_query, avg_rating_query, sessions_query]
        mock_db.query.side_effect = query_calls

        result = await get_platform_stats(mock_db)

        assert result.tutor_count == 10000
        assert result.student_count == 500000
        assert result.completed_sessions == 1000000


class TestGetFeaturedReviews:
    """Tests for the get_featured_reviews endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_review(self):
        """Create a mock review."""
        review = MagicMock()
        review.id = 1
        review.rating = 5
        review.comment = "Excellent tutor! Very patient and knowledgeable."
        review.student_id = 10
        review.created_at = datetime(2024, 1, 15)
        return review

    @pytest.fixture
    def mock_student(self):
        """Create a mock student user for review."""
        student = MagicMock()
        student.id = 10
        student.first_name = "John"
        student.last_name = "Doe"
        student.role = "student"
        return student

    @pytest.mark.asyncio
    async def test_get_featured_reviews_success(self, mock_db, mock_review, mock_student):
        """Test getting featured reviews successfully."""
        # Set up mock for reviews query
        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_review
        ]

        # Set up mock for total count query
        count_query = MagicMock()
        count_query.count.return_value = 25

        # Set up mock for user query (to get reviewer info)
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_student

        # Configure query calls
        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        assert isinstance(result, FeaturedReviewsResponse)
        assert result.total_reviews == 25
        assert len(result.reviews) == 1

        featured = result.reviews[0]
        assert isinstance(featured, FeaturedReview)
        assert featured.rating == 5
        assert featured.author == "John D."
        assert featured.role == "Student"
        assert featured.initials == "JD"
        assert "Excellent" in featured.quote

    @pytest.mark.asyncio
    async def test_get_featured_reviews_empty(self, mock_db):
        """Test getting featured reviews when none exist."""
        # Set up mock for empty reviews query
        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        count_query = MagicMock()
        count_query.count.return_value = 0

        mock_db.query.side_effect = [reviews_query, count_query]

        result = await get_featured_reviews(mock_db, limit=4)

        assert isinstance(result, FeaturedReviewsResponse)
        assert result.total_reviews == 0
        assert len(result.reviews) == 0

    @pytest.mark.asyncio
    async def test_get_featured_reviews_respects_limit(self, mock_db):
        """Test that the limit parameter is respected."""
        reviews = []
        students = []

        # Create 3 reviews
        for i in range(3):
            review = MagicMock()
            review.id = i + 1
            review.rating = 5
            review.comment = f"Great review {i}"
            review.student_id = 100 + i
            reviews.append(review)

            student = MagicMock()
            student.id = 100 + i
            student.first_name = f"Student{i}"
            student.last_name = f"Last{i}"
            student.role = "student"
            students.append(student)

        # Set up mocks
        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            reviews
        )

        count_query = MagicMock()
        count_query.count.return_value = 10

        # Each review needs a user lookup
        user_queries = []
        for student in students:
            user_query = MagicMock()
            user_query.filter.return_value.first.return_value = student
            user_queries.append(user_query)

        mock_db.query.side_effect = [reviews_query, count_query] + user_queries

        result = await get_featured_reviews(mock_db, limit=3)

        assert len(result.reviews) == 3
        assert result.total_reviews == 10

    @pytest.mark.asyncio
    async def test_get_featured_reviews_privacy_formatting(
        self, mock_db, mock_review, mock_student
    ):
        """Test that author name is formatted for privacy (First Last Initial)."""
        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_review
        ]

        count_query = MagicMock()
        count_query.count.return_value = 5

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_student

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        # Name should be "First L." format for privacy
        assert result.reviews[0].author == "John D."

    @pytest.mark.asyncio
    async def test_get_featured_reviews_missing_last_name(self, mock_db, mock_review):
        """Test handling student without last name."""
        student_no_last = MagicMock()
        student_no_last.id = 10
        student_no_last.first_name = "Jane"
        student_no_last.last_name = None
        student_no_last.role = "student"

        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_review
        ]

        count_query = MagicMock()
        count_query.count.return_value = 5

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = student_no_last

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        # Should just show first name
        assert result.reviews[0].author == "Jane"
        assert result.reviews[0].initials == "J"

    @pytest.mark.asyncio
    async def test_get_featured_reviews_missing_first_name(self, mock_db, mock_review):
        """Test handling student without first name."""
        student_no_first = MagicMock()
        student_no_first.id = 10
        student_no_first.first_name = None
        student_no_first.last_name = "Smith"
        student_no_first.role = "student"

        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_review
        ]

        count_query = MagicMock()
        count_query.count.return_value = 5

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = student_no_first

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        # Should show "Student S."
        assert result.reviews[0].author == "Student S."
        assert result.reviews[0].initials == "S"

    @pytest.mark.asyncio
    async def test_get_featured_reviews_missing_both_names(self, mock_db, mock_review):
        """Test handling student without any name."""
        student_no_name = MagicMock()
        student_no_name.id = 10
        student_no_name.first_name = None
        student_no_name.last_name = None
        student_no_name.role = "student"

        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_review
        ]

        count_query = MagicMock()
        count_query.count.return_value = 5

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = student_no_name

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        # Should show "Student" and "S" for default
        assert result.reviews[0].author == "Student"
        assert result.reviews[0].initials == "S"

    @pytest.mark.asyncio
    async def test_get_featured_reviews_long_comment_truncated(self, mock_db, mock_student):
        """Test that long comments are truncated to 300 characters."""
        long_comment = "A" * 500  # 500 character comment

        review_with_long_comment = MagicMock()
        review_with_long_comment.id = 1
        review_with_long_comment.rating = 5
        review_with_long_comment.comment = long_comment
        review_with_long_comment.student_id = 10

        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            review_with_long_comment
        ]

        count_query = MagicMock()
        count_query.count.return_value = 1

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = mock_student

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        # Comment should be truncated to 300 characters
        assert len(result.reviews[0].quote) == 300

    @pytest.mark.asyncio
    async def test_get_featured_reviews_skips_reviews_without_user(self, mock_db):
        """Test that reviews without a valid user are skipped."""
        review = MagicMock()
        review.id = 1
        review.rating = 5
        review.comment = "Great!"
        review.student_id = 999  # Non-existent user

        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            review
        ]

        count_query = MagicMock()
        count_query.count.return_value = 1

        # User not found
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = None

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        # Review should be skipped
        assert len(result.reviews) == 0
        assert result.total_reviews == 1

    @pytest.mark.asyncio
    async def test_get_featured_reviews_tutor_role(self, mock_db, mock_review):
        """Test that tutor users get correct role label."""
        tutor_reviewer = MagicMock()
        tutor_reviewer.id = 10
        tutor_reviewer.first_name = "Tutor"
        tutor_reviewer.last_name = "Name"
        tutor_reviewer.role = "tutor"

        reviews_query = MagicMock()
        reviews_query.join.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_review
        ]

        count_query = MagicMock()
        count_query.count.return_value = 5

        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = tutor_reviewer

        mock_db.query.side_effect = [reviews_query, count_query, user_query]

        result = await get_featured_reviews(mock_db, limit=4)

        assert result.reviews[0].role == "Tutor"


class TestPlatformStatsSchema:
    """Tests for the PlatformStats Pydantic schema."""

    def test_platform_stats_valid(self):
        """Test creating valid platform stats."""
        stats = PlatformStats(
            tutor_count=10,
            student_count=100,
            average_rating=4.5,
            completed_sessions=500,
            generated_at=datetime.now(),
        )
        assert stats.tutor_count == 10
        assert stats.student_count == 100
        assert stats.average_rating == 4.5
        assert stats.completed_sessions == 500

    def test_platform_stats_zero_values(self):
        """Test platform stats with zero values."""
        stats = PlatformStats(
            tutor_count=0,
            student_count=0,
            average_rating=0.0,
            completed_sessions=0,
            generated_at=datetime.now(),
        )
        assert stats.tutor_count == 0
        assert stats.student_count == 0
        assert stats.average_rating == 0.0
        assert stats.completed_sessions == 0


class TestFeaturedReviewSchema:
    """Tests for the FeaturedReview Pydantic schema."""

    def test_featured_review_valid(self):
        """Test creating valid featured review."""
        review = FeaturedReview(
            quote="Great tutor!",
            author="John D.",
            role="Student",
            rating=5,
            initials="JD",
            tutor_name="Jane Smith",
        )
        assert review.quote == "Great tutor!"
        assert review.author == "John D."
        assert review.role == "Student"
        assert review.rating == 5
        assert review.initials == "JD"
        assert review.tutor_name == "Jane Smith"

    def test_featured_review_without_tutor_name(self):
        """Test featured review without tutor name (optional)."""
        review = FeaturedReview(
            quote="Amazing experience!",
            author="Alice B.",
            role="Student",
            rating=4,
            initials="AB",
        )
        assert review.tutor_name is None


class TestFeaturedReviewsResponseSchema:
    """Tests for the FeaturedReviewsResponse Pydantic schema."""

    def test_featured_reviews_response_valid(self):
        """Test creating valid featured reviews response."""
        review = FeaturedReview(
            quote="Excellent!",
            author="Bob C.",
            role="Student",
            rating=5,
            initials="BC",
        )
        response = FeaturedReviewsResponse(
            reviews=[review],
            total_reviews=100,
        )
        assert len(response.reviews) == 1
        assert response.total_reviews == 100

    def test_featured_reviews_response_empty(self):
        """Test featured reviews response with empty list."""
        response = FeaturedReviewsResponse(
            reviews=[],
            total_reviews=0,
        )
        assert len(response.reviews) == 0
        assert response.total_reviews == 0
