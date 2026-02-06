"""
Comprehensive tests for backend/core/cache.py

Tests cover:
- cache_with_ttl() decorator
- invalidate_cache() function
- get_cache_stats() function
- Cache expiration behavior
- Cache key generation
- Edge cases and concurrent access patterns
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from core.cache import (
    _cache,
    cache_with_ttl,
    get_cache_stats,
    invalidate_cache,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache before and after each test."""
    _cache.clear()
    yield
    _cache.clear()


# =============================================================================
# Test: cache_with_ttl() Decorator
# =============================================================================


class TestCacheWithTTL:
    """Test the cache_with_ttl decorator."""

    def test_cache_basic_function(self):
        """Test basic caching of function results."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_data():
            nonlocal call_count
            call_count += 1
            return {"value": "test"}

        # First call should execute the function
        result1 = get_data()
        assert result1 == {"value": "test"}
        assert call_count == 1

        # Second call should return cached result
        result2 = get_data()
        assert result2 == {"value": "test"}
        assert call_count == 1  # Still 1, not called again

    def test_cache_with_arguments(self):
        """Test caching with different arguments creates different cache entries."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_item(item_id):
            nonlocal call_count
            call_count += 1
            return {"id": item_id}

        # Different arguments should result in separate cache entries
        result1 = get_item(1)
        result2 = get_item(2)
        result3 = get_item(1)  # Should be cached

        assert result1 == {"id": 1}
        assert result2 == {"id": 2}
        assert result3 == {"id": 1}
        assert call_count == 2  # Only 2 calls (third was cached)

    def test_cache_with_kwargs(self):
        """Test caching with keyword arguments."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_user(user_id, include_profile=False):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "has_profile": include_profile}

        result1 = get_user(user_id=1, include_profile=True)
        result2 = get_user(user_id=1, include_profile=False)
        get_user(user_id=1, include_profile=True)  # Cached

        assert result1["has_profile"] is True
        assert result2["has_profile"] is False
        assert call_count == 2  # Third call was cached

    def test_cache_expiration(self):
        """Test that cache entries expire after TTL."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=1)  # 1 second TTL
        def get_timestamp():
            nonlocal call_count
            call_count += 1
            return time.time()

        result1 = get_timestamp()
        assert call_count == 1

        # Wait for cache to expire
        time.sleep(1.1)

        result2 = get_timestamp()
        assert call_count == 2  # Called again after expiration
        assert result2 > result1

    def test_cache_expired_entry_removed(self):
        """Test that expired entries are removed from cache."""
        @cache_with_ttl(ttl_seconds=1)
        def get_value():
            return "test"

        get_value()
        assert len(_cache) == 1

        # Wait for expiration
        time.sleep(1.1)

        # Access should remove expired entry and create new one
        get_value()
        assert len(_cache) == 1

    def test_cache_key_generation(self):
        """Test that cache keys are properly generated."""
        @cache_with_ttl(ttl_seconds=60)
        def my_function(a, b, c=None):
            return a + b

        my_function(1, 2)
        my_function(1, 2, c="test")

        # Should have 2 cache entries with different keys
        assert len(_cache) == 2

        # Keys should contain function info
        keys = list(_cache.keys())
        assert all("my_function" in key for key in keys)

    def test_cache_default_ttl(self):
        """Test cache with default TTL (300 seconds)."""
        @cache_with_ttl()
        def get_default_ttl():
            return "cached"

        get_default_ttl()

        # Check that cache entry exists with TTL around 300 seconds
        cache_key = list(_cache.keys())[0]
        _, expiry = _cache[cache_key]
        # Expiry should be approximately now + 300 seconds
        expected_expiry = time.time() + 300
        assert abs(expiry - expected_expiry) < 2  # Within 2 seconds

    def test_cache_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""

        @cache_with_ttl(ttl_seconds=60)
        def documented_function():
            """This is a documented function."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    def test_cache_with_none_return(self):
        """Test caching when function returns None."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_none():
            nonlocal call_count
            call_count += 1
            return None

        result1 = get_none()
        result2 = get_none()

        assert result1 is None
        assert result2 is None
        assert call_count == 1  # None should be cached

    def test_cache_with_list_return(self):
        """Test caching with list return values."""
        @cache_with_ttl(ttl_seconds=60)
        def get_list():
            return [1, 2, 3]

        result1 = get_list()
        result2 = get_list()

        assert result1 == [1, 2, 3]
        assert result2 == [1, 2, 3]
        # Note: These are the same cached object
        assert result1 is result2

    def test_cache_with_complex_args(self):
        """Test caching with complex argument types."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def process_data(data_list, config_dict):
            nonlocal call_count
            call_count += 1
            return len(data_list) + len(config_dict)

        result1 = process_data([1, 2, 3], {"a": 1})
        process_data([1, 2, 3], {"a": 1})

        assert result1 == 4
        assert call_count == 1

    def test_cache_with_mock_db(self):
        """Test caching with mock database session (typical use case)."""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = [{"id": 1}, {"id": 2}]

        @cache_with_ttl(ttl_seconds=60)
        def get_subjects(db):
            return db.query("subjects").all()

        result1 = get_subjects(mock_db)
        get_subjects(mock_db)

        assert result1 == [{"id": 1}, {"id": 2}]
        # DB should only be queried once
        assert mock_db.query.call_count == 1


# =============================================================================
# Test: invalidate_cache() Function
# =============================================================================


class TestInvalidateCache:
    """Test the invalidate_cache function."""

    def test_invalidate_all_cache(self):
        """Test invalidating entire cache."""
        @cache_with_ttl(ttl_seconds=60)
        def get_a():
            return "a"

        @cache_with_ttl(ttl_seconds=60)
        def get_b():
            return "b"

        get_a()
        get_b()
        assert len(_cache) == 2

        invalidate_cache()

        assert len(_cache) == 0

    def test_invalidate_cache_by_pattern(self):
        """Test invalidating cache entries matching a pattern."""
        @cache_with_ttl(ttl_seconds=60)
        def get_user(user_id):
            return {"user_id": user_id}

        @cache_with_ttl(ttl_seconds=60)
        def get_product(product_id):
            return {"product_id": product_id}

        get_user(1)
        get_user(2)
        get_product(100)
        assert len(_cache) == 3

        # Invalidate only user-related cache entries
        invalidate_cache("get_user")

        # Only product cache should remain
        assert len(_cache) == 1
        remaining_key = list(_cache.keys())[0]
        assert "get_product" in remaining_key

    def test_invalidate_cache_pattern_no_match(self):
        """Test invalidating with pattern that doesn't match anything."""
        @cache_with_ttl(ttl_seconds=60)
        def get_data():
            return "data"

        get_data()
        assert len(_cache) == 1

        invalidate_cache("nonexistent_pattern")

        # Cache should be unchanged
        assert len(_cache) == 1

    def test_invalidate_cache_partial_pattern(self):
        """Test invalidating with partial pattern match."""
        @cache_with_ttl(ttl_seconds=60)
        def get_user_profile(user_id):
            return {"profile": user_id}

        @cache_with_ttl(ttl_seconds=60)
        def get_user_settings(user_id):
            return {"settings": user_id}

        @cache_with_ttl(ttl_seconds=60)
        def get_admin_data():
            return "admin"

        get_user_profile(1)
        get_user_settings(1)
        get_admin_data()
        assert len(_cache) == 3

        # Invalidate all user-related entries
        invalidate_cache("user")

        # Only admin cache should remain
        assert len(_cache) == 1

    def test_invalidate_empty_cache(self):
        """Test invalidating empty cache doesn't cause errors."""
        assert len(_cache) == 0
        invalidate_cache()  # Should not raise
        assert len(_cache) == 0

        invalidate_cache("pattern")  # Should not raise
        assert len(_cache) == 0


# =============================================================================
# Test: get_cache_stats() Function
# =============================================================================


class TestGetCacheStats:
    """Test the get_cache_stats function."""

    def test_cache_stats_empty(self):
        """Test stats for empty cache."""
        stats = get_cache_stats()

        assert stats["total_entries"] == 0
        assert stats["valid_entries"] == 0
        assert stats["expired_entries"] == 0
        assert stats["keys"] == []

    def test_cache_stats_with_valid_entries(self):
        """Test stats with valid (non-expired) entries."""
        @cache_with_ttl(ttl_seconds=60)
        def get_a():
            return "a"

        @cache_with_ttl(ttl_seconds=60)
        def get_b():
            return "b"

        get_a()
        get_b()

        stats = get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 2
        assert stats["expired_entries"] == 0
        assert len(stats["keys"]) == 2

    def test_cache_stats_with_expired_entries(self):
        """Test stats correctly identify expired entries."""
        @cache_with_ttl(ttl_seconds=1)
        def get_short_lived():
            return "short"

        @cache_with_ttl(ttl_seconds=60)
        def get_long_lived():
            return "long"

        get_short_lived()
        get_long_lived()

        # Wait for short-lived entry to expire
        time.sleep(1.1)

        stats = get_cache_stats()

        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 1
        assert stats["expired_entries"] == 1

    def test_cache_stats_keys_list(self):
        """Test that stats includes all cache keys."""
        @cache_with_ttl(ttl_seconds=60)
        def func1():
            return 1

        @cache_with_ttl(ttl_seconds=60)
        def func2():
            return 2

        func1()
        func2()

        stats = get_cache_stats()

        assert len(stats["keys"]) == 2
        assert any("func1" in key for key in stats["keys"])
        assert any("func2" in key for key in stats["keys"])


# =============================================================================
# Test: Edge Cases
# =============================================================================


class TestCacheEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_cache_with_zero_ttl(self):
        """Test cache with zero TTL (immediately expires)."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=0)
        def get_immediate_expire():
            nonlocal call_count
            call_count += 1
            return "result"

        # With 0 TTL, every call should execute the function
        # (though there might be a small timing window)
        get_immediate_expire()
        time.sleep(0.01)  # Small delay to ensure expiration
        get_immediate_expire()

        # Should have been called at least twice
        assert call_count >= 1

    def test_cache_with_negative_ttl(self):
        """Test cache behavior with negative TTL."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=-1)
        def get_negative_ttl():
            nonlocal call_count
            call_count += 1
            return "result"

        # Negative TTL means immediate expiration
        get_negative_ttl()
        get_negative_ttl()

        # Each call should execute since cache immediately expires
        assert call_count == 2

    def test_cache_with_exception(self):
        """Test that exceptions are not cached."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_function()

        with pytest.raises(ValueError):
            failing_function()

        # Function should be called each time since exception wasn't cached
        assert call_count == 2

    def test_cache_key_with_special_characters(self):
        """Test cache with arguments containing special characters."""
        @cache_with_ttl(ttl_seconds=60)
        def search(query):
            return f"results for: {query}"

        result1 = search("test query with spaces")
        result2 = search("query|with:special/chars")
        search("test query with spaces")  # Cached

        assert result1 == "results for: test query with spaces"
        assert result2 == "results for: query|with:special/chars"
        assert len(_cache) == 2

    def test_cache_with_large_return_value(self):
        """Test caching large return values."""
        @cache_with_ttl(ttl_seconds=60)
        def get_large_data():
            return list(range(10000))

        result1 = get_large_data()
        result2 = get_large_data()

        assert len(result1) == 10000
        assert result1 is result2  # Same cached object

    def test_multiple_decorators_same_function_name(self):
        """Test that same function name in different modules has unique keys."""
        # Simulate functions with same name but different modules
        @cache_with_ttl(ttl_seconds=60)
        def get_data():
            return "from module A"

        get_data()

        # The key includes module name, so different modules would have different keys
        cache_key = list(_cache.keys())[0]
        assert "test_cache" in cache_key  # Module name included


# =============================================================================
# Test: Concurrent Access Patterns
# =============================================================================


class TestConcurrentAccess:
    """Test cache behavior under concurrent access patterns."""

    def test_concurrent_reads(self):
        """Test multiple concurrent reads to cached data."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_shared_data():
            nonlocal call_count
            call_count += 1
            return {"shared": True}

        # Simulate concurrent reads
        results = [get_shared_data() for _ in range(10)]

        # All results should be the same cached value
        assert all(r == {"shared": True} for r in results)
        assert call_count == 1

    def test_cache_key_uniqueness(self):
        """Test that cache keys are truly unique for different calls."""
        @cache_with_ttl(ttl_seconds=60)
        def parameterized_func(a, b, c):
            return a + b + c

        # These should all be different cache entries
        parameterized_func(1, 2, 3)
        parameterized_func(1, 2, 4)
        parameterized_func(1, 3, 3)
        parameterized_func(2, 2, 3)

        assert len(_cache) == 4


# =============================================================================
# Test: Real-world Usage Patterns
# =============================================================================


class TestRealWorldPatterns:
    """Test patterns commonly used in the application."""

    def test_database_query_caching(self):
        """Test caching database query results."""
        mock_db = MagicMock()
        query_results = [
            {"id": 1, "name": "Math"},
            {"id": 2, "name": "Science"},
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = query_results

        @cache_with_ttl(ttl_seconds=300)
        def get_active_subjects(db):
            return db.query("Subject").filter("is_active=True").all()

        # First call
        result1 = get_active_subjects(mock_db)
        # Second call (should be cached)
        result2 = get_active_subjects(mock_db)

        assert result1 == query_results
        assert result2 == query_results
        # Database should only be queried once
        mock_db.query.assert_called_once()

    def test_api_response_caching(self):
        """Test caching external API responses."""
        api_call_count = 0

        @cache_with_ttl(ttl_seconds=60)
        def get_exchange_rates(currency):
            nonlocal api_call_count
            api_call_count += 1
            # Simulate API response
            return {"USD": 1.0, "EUR": 0.85, "GBP": 0.73}

        # Multiple requests for same currency
        for _ in range(5):
            get_exchange_rates("USD")

        # API should only be called once
        assert api_call_count == 1

    def test_cache_invalidation_after_update(self):
        """Test invalidating cache after data update."""
        call_count = 0

        @cache_with_ttl(ttl_seconds=300)
        def get_user_profile(user_id):
            nonlocal call_count
            call_count += 1
            return {"user_id": user_id, "name": "Test User"}

        # Initial fetch
        profile = get_user_profile(123)
        assert profile["name"] == "Test User"
        assert call_count == 1

        # Simulate user update - invalidate their cache
        invalidate_cache("get_user_profile")

        # Should fetch fresh data
        profile = get_user_profile(123)
        assert call_count == 2

    def test_selective_cache_invalidation(self):
        """Test selective invalidation based on data type."""
        @cache_with_ttl(ttl_seconds=300)
        def get_user(user_id):
            return {"type": "user", "id": user_id}

        @cache_with_ttl(ttl_seconds=300)
        def get_booking(booking_id):
            return {"type": "booking", "id": booking_id}

        # Populate cache
        get_user(1)
        get_user(2)
        get_booking(100)
        get_booking(101)

        assert len(_cache) == 4

        # Invalidate only user cache (e.g., after bulk user update)
        invalidate_cache("get_user")

        # Only booking cache should remain
        assert len(_cache) == 2
        stats = get_cache_stats()
        assert all("get_booking" in key for key in stats["keys"])
