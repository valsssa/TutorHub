"""
Cache Port - Interface for caching and distributed locking.

This port defines the contract for caching operations and distributed
locks, abstracting away the specific cache provider (Redis, etc.).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Protocol


@dataclass(frozen=True)
class CacheResult:
    """Result of a cache operation."""

    success: bool
    value: Any = None
    error_message: str | None = None


@dataclass(frozen=True)
class LockResult:
    """Result of a lock operation."""

    acquired: bool
    lock_token: str | None = None
    error_message: str | None = None


class CachePort(Protocol):
    """
    Protocol for caching and distributed locking operations.

    Implementations should handle:
    - Key-value storage with TTL
    - Atomic operations
    - Distributed locks for multi-instance deployments
    - Proper error handling
    """

    async def get(self, key: str) -> Any | None:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl_seconds: Time to live in seconds (None for no expiry)

        Returns:
            True if successful, False otherwise
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if key didn't exist
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        ...

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.

        Args:
            keys: List of cache keys

        Returns:
            Dict of key -> value (missing keys not included)
        """
        ...

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """
        Set multiple values in cache.

        Args:
            mapping: Dict of key -> value
            ttl_seconds: Time to live in seconds

        Returns:
            True if all successful
        """
        ...

    async def delete_many(self, keys: list[str]) -> int:
        """
        Delete multiple keys from cache.

        Args:
            keys: List of cache keys

        Returns:
            Number of keys deleted
        """
        ...

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")

        Returns:
            Number of keys deleted
        """
        ...

    async def increment(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """
        Atomically increment a value.

        Args:
            key: Cache key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        ...

    async def decrement(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """
        Atomically decrement a value.

        Args:
            key: Cache key
            amount: Amount to decrement by

        Returns:
            New value after decrement
        """
        ...

    async def get_ttl(self, key: str) -> int | None:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining seconds, None if no expiry, -2 if key doesn't exist
        """
        ...

    async def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """
        Set TTL on an existing key.

        Args:
            key: Cache key
            ttl_seconds: New TTL in seconds

        Returns:
            True if successful, False if key doesn't exist
        """
        ...

    # ============================================================================
    # Distributed Locking
    # ============================================================================

    async def acquire_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
        blocking: bool = False,
        blocking_timeout: float | None = None,
    ) -> LockResult:
        """
        Acquire a distributed lock.

        Args:
            lock_name: Name of the lock
            ttl_seconds: Lock expiration time (prevents deadlocks)
            blocking: If True, wait for lock; if False, return immediately
            blocking_timeout: Max time to wait for lock (only if blocking=True)

        Returns:
            LockResult with acquired status and lock_token
        """
        ...

    async def release_lock(
        self,
        lock_name: str,
        lock_token: str,
    ) -> bool:
        """
        Release a distributed lock.

        Args:
            lock_name: Name of the lock
            lock_token: Token received when lock was acquired

        Returns:
            True if lock was released, False if lock didn't exist or wrong token
        """
        ...

    async def extend_lock(
        self,
        lock_name: str,
        lock_token: str,
        additional_seconds: int,
    ) -> bool:
        """
        Extend the TTL of a held lock.

        Args:
            lock_name: Name of the lock
            lock_token: Token received when lock was acquired
            additional_seconds: Seconds to add to lock TTL

        Returns:
            True if extended, False if lock doesn't exist or wrong token
        """
        ...

    @asynccontextmanager
    async def distributed_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
    ) -> AsyncIterator[bool]:
        """
        Context manager for distributed locking.

        Usage:
            async with cache.distributed_lock("job:my_job") as acquired:
                if not acquired:
                    return  # Lock not acquired, skip
                # ... do work ...

        Args:
            lock_name: Name of the lock
            ttl_seconds: Lock expiration time

        Yields:
            True if lock acquired, False otherwise
        """
        ...

    # ============================================================================
    # Health and Stats
    # ============================================================================

    async def ping(self) -> bool:
        """
        Check if cache is available.

        Returns:
            True if cache is responding
        """
        ...

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (keys, memory, etc.)
        """
        ...

    async def flush_all(self) -> bool:
        """
        Clear all cache data (use with caution!).

        Returns:
            True if successful
        """
        ...
