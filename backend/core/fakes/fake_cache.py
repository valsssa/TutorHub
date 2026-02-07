"""
Fake Cache - In-memory implementation of CachePort for testing.

Provides TTL tracking, lock simulation, and operation history for assertions.
"""

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime

from core.datetime_utils import utc_now
from typing import Any

from core.ports.cache import LockResult


@dataclass
class CacheEntry:
    """A cached value with expiration."""

    value: Any
    expires_at: float | None = None  # None means no expiry

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class LockEntry:
    """A held lock."""

    lock_token: str
    expires_at: float


@dataclass
class CacheOperation:
    """Record of a cache operation."""

    operation: str
    key: str
    timestamp: datetime = field(default_factory=lambda: utc_now())
    metadata: dict = field(default_factory=dict)


@dataclass
class FakeCache:
    """
    In-memory fake implementation of CachePort for testing.

    Features:
    - TTL tracking with expiration
    - Lock simulation with token ownership
    - Operation history for assertions
    - Configurable failure modes
    """

    cache: dict[str, CacheEntry] = field(default_factory=dict)
    locks: dict[str, LockEntry] = field(default_factory=dict)
    operations: list[CacheOperation] = field(default_factory=list)
    should_fail: bool = False
    lock_should_fail: bool = False
    instance_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def _record_operation(
        self,
        operation: str,
        key: str,
        metadata: dict | None = None,
    ) -> None:
        """Record a cache operation."""
        self.operations.append(
            CacheOperation(
                operation=operation,
                key=key,
                metadata=metadata or {},
            )
        )

    def _clean_expired(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]

        expired_locks = [k for k, v in self.locks.items() if now > v.expires_at]
        for key in expired_locks:
            del self.locks[key]

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        self._record_operation("get", key)
        self._clean_expired()

        if self.should_fail:
            return None

        entry = self.cache.get(key)
        if entry is None or entry.is_expired():
            return None
        return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set a value in cache."""
        self._record_operation("set", key, {"ttl": ttl_seconds})

        if self.should_fail:
            return False

        expires_at = None
        if ttl_seconds:
            expires_at = time.time() + ttl_seconds

        self.cache[key] = CacheEntry(value=value, expires_at=expires_at)
        return True

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        self._record_operation("delete", key)

        if self.should_fail:
            return False

        if key in self.cache:
            del self.cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        self._record_operation("exists", key)
        self._clean_expired()

        if self.should_fail:
            return False

        entry = self.cache.get(key)
        return entry is not None and not entry.is_expired()

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        self._record_operation("get_many", ",".join(keys))
        self._clean_expired()

        if self.should_fail:
            return {}

        result = {}
        for key in keys:
            entry = self.cache.get(key)
            if entry and not entry.is_expired():
                result[key] = entry.value
        return result

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set multiple values in cache."""
        self._record_operation("set_many", ",".join(mapping.keys()), {"ttl": ttl_seconds})

        if self.should_fail:
            return False

        expires_at = None
        if ttl_seconds:
            expires_at = time.time() + ttl_seconds

        for key, value in mapping.items():
            self.cache[key] = CacheEntry(value=value, expires_at=expires_at)
        return True

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys from cache."""
        self._record_operation("delete_many", ",".join(keys))

        if self.should_fail:
            return 0

        count = 0
        for key in keys:
            if key in self.cache:
                del self.cache[key]
                count += 1
        return count

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        self._record_operation("delete_pattern", pattern)

        if self.should_fail:
            return 0

        # Simple wildcard matching
        import fnmatch

        keys_to_delete = [k for k in self.cache if fnmatch.fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self.cache[key]
        return len(keys_to_delete)

    async def increment(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """Atomically increment a value."""
        self._record_operation("increment", key, {"amount": amount})

        if self.should_fail:
            return 0

        entry = self.cache.get(key)
        if entry is None or entry.is_expired():
            self.cache[key] = CacheEntry(value=amount)
            return amount

        new_value = int(entry.value) + amount
        entry.value = new_value
        return new_value

    async def decrement(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """Atomically decrement a value."""
        return await self.increment(key, -amount)

    async def get_ttl(self, key: str) -> int | None:
        """Get remaining TTL for a key."""
        self._record_operation("get_ttl", key)

        entry = self.cache.get(key)
        if entry is None:
            return -2  # Key doesn't exist

        if entry.expires_at is None:
            return None  # No expiry

        remaining = int(entry.expires_at - time.time())
        return max(0, remaining)

    async def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """Set TTL on an existing key."""
        self._record_operation("set_ttl", key, {"ttl": ttl_seconds})

        entry = self.cache.get(key)
        if entry is None:
            return False

        entry.expires_at = time.time() + ttl_seconds
        return True

    # =========================================================================
    # Distributed Locking
    # =========================================================================

    async def acquire_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
        blocking: bool = False,
        blocking_timeout: float | None = None,
    ) -> LockResult:
        """Acquire a distributed lock."""
        self._record_operation("acquire_lock", lock_name, {"ttl": ttl_seconds})
        self._clean_expired()

        if self.lock_should_fail:
            # Fail-open like the real implementation
            return LockResult(acquired=True, lock_token=None)

        if lock_name in self.locks:
            if not blocking:
                return LockResult(acquired=False)

            # Blocking mode - simulate waiting
            import asyncio

            start = time.time()
            timeout = blocking_timeout or 30.0

            while time.time() - start < timeout:
                await asyncio.sleep(0.01)  # Fast polling for tests
                self._clean_expired()
                if lock_name not in self.locks:
                    break

            if lock_name in self.locks:
                return LockResult(
                    acquired=False,
                    error_message="Lock acquisition timed out",
                )

        lock_token = f"{self.instance_id}:{uuid.uuid4().hex[:8]}"
        self.locks[lock_name] = LockEntry(
            lock_token=lock_token,
            expires_at=time.time() + ttl_seconds,
        )

        return LockResult(acquired=True, lock_token=lock_token)

    async def release_lock(
        self,
        lock_name: str,
        lock_token: str,
    ) -> bool:
        """Release a distributed lock."""
        self._record_operation("release_lock", lock_name)

        if not lock_token:
            return True

        lock = self.locks.get(lock_name)
        if lock is None:
            return False

        if lock.lock_token != lock_token:
            return False

        del self.locks[lock_name]
        return True

    async def extend_lock(
        self,
        lock_name: str,
        lock_token: str,
        additional_seconds: int,
    ) -> bool:
        """Extend the TTL of a held lock."""
        self._record_operation(
            "extend_lock", lock_name, {"additional_seconds": additional_seconds}
        )

        if not lock_token:
            return False

        lock = self.locks.get(lock_name)
        if lock is None or lock.lock_token != lock_token:
            return False

        lock.expires_at = time.time() + additional_seconds
        return True

    @asynccontextmanager
    async def distributed_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
    ) -> AsyncIterator[bool]:
        """Context manager for distributed locking."""
        result = await self.acquire_lock(lock_name, ttl_seconds)
        try:
            yield result.acquired
        finally:
            if result.acquired and result.lock_token:
                await self.release_lock(lock_name, result.lock_token)

    # =========================================================================
    # Health and Stats
    # =========================================================================

    async def ping(self) -> bool:
        """Check if cache is available."""
        return not self.should_fail

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        self._clean_expired()
        return {
            "total_keys": len(self.cache),
            "total_locks": len(self.locks),
            "operations_count": len(self.operations),
        }

    async def flush_all(self) -> bool:
        """Clear all cache data."""
        self._record_operation("flush_all", "*")
        self.cache.clear()
        self.locks.clear()
        return True

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def get_operations(self, operation: str) -> list[CacheOperation]:
        """Get all operations of a specific type."""
        return [o for o in self.operations if o.operation == operation]

    def is_locked(self, lock_name: str) -> bool:
        """Check if a lock is held (for testing)."""
        self._clean_expired()
        return lock_name in self.locks

    def force_expire(self, key: str) -> None:
        """Force a key to expire (for testing)."""
        if key in self.cache:
            self.cache[key].expires_at = time.time() - 1

    def reset(self) -> None:
        """Reset all state."""
        self.cache.clear()
        self.locks.clear()
        self.operations.clear()
        self.should_fail = False
        self.lock_should_fail = False
