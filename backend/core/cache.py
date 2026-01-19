"""Simple in-memory caching utilities for frequently accessed data."""

import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

# Simple in-memory cache with TTL
_cache: Dict[str, Tuple[Any, float]] = {}


def cache_with_ttl(ttl_seconds: int = 300):
    """
    Decorator to cache function results with TTL (Time To Live).

    Args:
        ttl_seconds: Cache duration in seconds (default: 5 minutes)

    Usage:
        @cache_with_ttl(ttl_seconds=300)
        def get_subjects(db):
            return db.query(Subject).all()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__module__}.{func.__name__}:{str(args)}:{str(kwargs)}"

            # Check if cached and still valid
            if cache_key in _cache:
                cached_value, expiry_time = _cache[cache_key]
                if time.time() < expiry_time:
                    return cached_value
                else:
                    # Expired, remove from cache
                    del _cache[cache_key]

            # Not cached or expired - compute value
            result = func(*args, **kwargs)

            # Store in cache with expiry time
            _cache[cache_key] = (result, time.time() + ttl_seconds)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: Optional[str] = None) -> None:
    """
    Invalidate cached entries.

    Args:
        pattern: If provided, only invalidate keys containing this pattern.
                 If None, invalidate all cache.
    """
    if pattern is None:
        _cache.clear()
    else:
        keys_to_remove = [key for key in _cache if pattern in key]
        for key in keys_to_remove:
            del _cache[key]


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring."""
    now = time.time()
    valid_entries = sum(1 for _, expiry in _cache.values() if expiry > now)
    expired_entries = len(_cache) - valid_entries

    return {
        "total_entries": len(_cache),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
        "keys": list(_cache.keys()),
    }
