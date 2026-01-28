"""Tests for core utility functions."""

from datetime import datetime

from core.cache import cache_with_ttl, get_cache_stats, invalidate_cache
from core.pagination import PaginationParams, paginate
from core.sanitization import sanitize_email, sanitize_text_input, sanitize_url


class TestSanitization:
    """Test input sanitization functions."""

    def test_sanitize_text_strips_whitespace(self):
        """Test that text sanitization strips leading/trailing whitespace."""
        result = sanitize_text_input("  hello world  ")
        assert result == "hello world"

    def test_sanitize_text_limits_length(self):
        """Test that text sanitization enforces max length."""
        long_text = "a" * 200
        result = sanitize_text_input(long_text, max_length=100)
        assert len(result) == 100

    def test_sanitize_text_removes_null_bytes(self):
        """Test that null bytes are removed."""
        text_with_null = "hello\x00world"
        result = sanitize_text_input(text_with_null)
        assert "\x00" not in result
        assert "hello" in result

    def test_sanitize_text_handles_none(self):
        """Test that None input returns empty string."""
        result = sanitize_text_input(None)
        assert result == ""

    def test_sanitize_text_handles_empty_string(self):
        """Test that empty string stays empty."""
        result = sanitize_text_input("")
        assert result == ""

    def test_sanitize_url_valid_http(self):
        """Test that valid HTTP URLs are accepted."""
        url = "http://example.com/path"
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_valid_https(self):
        """Test that valid HTTPS URLs are accepted."""
        url = "https://example.com/path"
        result = sanitize_url(url)
        assert result == url

    def test_sanitize_url_rejects_javascript(self):
        """Test that javascript: URLs are rejected."""
        url = "javascript:alert('xss')"
        result = sanitize_url(url)
        assert result is None

    def test_sanitize_url_rejects_data(self):
        """Test that data: URLs are rejected."""
        url = "data:text/html,<script>alert('xss')</script>"
        result = sanitize_url(url)
        assert result is None

    def test_sanitize_url_handles_invalid_urls(self):
        """Test that invalid URLs return None."""
        result = sanitize_url("not a url")
        assert result is None

    def test_sanitize_email_lowercase(self):
        """Test that emails are converted to lowercase."""
        result = sanitize_email("Test.User@EXAMPLE.COM")
        assert result == "test.user@example.com"

    def test_sanitize_email_strips_whitespace(self):
        """Test that email whitespace is stripped."""
        result = sanitize_email("  test@example.com  ")
        assert result == "test@example.com"


class TestPagination:
    """Test pagination utilities."""

    def test_pagination_params_defaults(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_pagination_params_custom(self):
        """Test custom pagination parameters."""
        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50

    def test_paginate_first_page(self, db_session):
        """Test pagination of first page."""
        from models import Subject

        # Create test subjects
        for i in range(25):
            subject = Subject(name=f"Subject {i}", is_active=True)
            db_session.add(subject)
        db_session.commit()

        query = db_session.query(Subject)
        result = paginate(query, page=1, page_size=10)

        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total"] == 25
        assert len(result["items"]) == 10
        assert result["items"][0].name == "Subject 0"

    def test_paginate_second_page(self, db_session):
        """Test pagination of second page."""
        from models import Subject

        # Create test subjects
        for i in range(25):
            subject = Subject(name=f"Subject {i}", is_active=True)
            db_session.add(subject)
        db_session.commit()

        query = db_session.query(Subject)
        result = paginate(query, page=2, page_size=10)

        assert result["page"] == 2
        assert len(result["items"]) == 10
        assert result["items"][0].name == "Subject 10"

    def test_paginate_last_page_partial(self, db_session):
        """Test pagination of last page with partial results."""
        from models import Subject

        # Create 25 subjects
        for i in range(25):
            subject = Subject(name=f"Subject {i}", is_active=True)
            db_session.add(subject)
        db_session.commit()

        query = db_session.query(Subject)
        result = paginate(query, page=3, page_size=10)

        assert result["page"] == 3
        assert len(result["items"]) == 5  # Only 5 remaining


class TestCaching:
    """Test caching utilities."""

    def test_cache_stores_value(self):
        """Test that cache stores and retrieves values."""

        @cache_with_ttl(ttl_seconds=60)
        def expensive_function(x):
            return x * 2

        # Clear cache before test
        invalidate_cache()

        result1 = expensive_function(5)
        result2 = expensive_function(5)

        assert result1 == 10
        assert result2 == 10

    def test_cache_different_args(self):
        """Test that cache handles different arguments."""

        @cache_with_ttl(ttl_seconds=60)
        def expensive_function(x):
            return x * 2

        invalidate_cache()

        result1 = expensive_function(5)
        result2 = expensive_function(10)

        assert result1 == 10
        assert result2 == 20

    def test_cache_expiration(self):
        """Test that cache entries expire."""
        import time

        @cache_with_ttl(ttl_seconds=1)
        def expensive_function(x):
            return x * 2 + datetime.now().microsecond

        invalidate_cache()

        result1 = expensive_function(5)
        time.sleep(2)  # Wait for cache to expire
        result2 = expensive_function(5)

        # Results should be different after expiration
        # (function adds current microsecond)
        assert result1 != result2

    def test_cache_invalidation(self):
        """Test cache invalidation."""

        @cache_with_ttl(ttl_seconds=60)
        def expensive_function(x):
            return x * 2

        invalidate_cache()

        expensive_function(5)

        stats_before = get_cache_stats()
        assert stats_before["total_entries"] > 0

        invalidate_cache()

        stats_after = get_cache_stats()
        assert stats_after["total_entries"] == 0

    def test_cache_pattern_invalidation(self):
        """Test pattern-based cache invalidation."""

        @cache_with_ttl(ttl_seconds=60)
        def function_a(x):
            return x * 2

        @cache_with_ttl(ttl_seconds=60)
        def function_b(x):
            return x * 3

        invalidate_cache()

        function_a(5)
        function_b(5)

        stats = get_cache_stats()
        initial_count = stats["total_entries"]

        # Invalidate only function_a
        invalidate_cache(pattern="function_a")

        stats_after = get_cache_stats()
        # Should have fewer entries
        assert stats_after["total_entries"] < initial_count

    def test_cache_stats(self):
        """Test cache statistics."""

        @cache_with_ttl(ttl_seconds=60)
        def expensive_function(x):
            return x * 2

        invalidate_cache()

        expensive_function(1)
        expensive_function(2)
        expensive_function(3)

        stats = get_cache_stats()

        assert "total_entries" in stats
        assert "valid_entries" in stats
        assert "expired_entries" in stats
        assert "keys" in stats
        assert stats["total_entries"] >= 3
